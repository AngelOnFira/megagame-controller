#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Main entry point for the bot.

This module performs the start-up, login and reads out the settings to configure
the bot.
"""
import logging
from importlib import import_module

import os
import discord
import django
import time
from django.conf import settings
from discord.ext import tasks
import asyncio

from bot.plugins.base import MethodPool
from bot.plugins.events import EventPool
from asgiref.sync import sync_to_async, async_to_sync

logger = logging.getLogger("bot")

intents = discord.Intents.default()
intents.members = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    from bot.users.services import CreateMember

    from bot.discord_guilds.models import Guild
    from bot.discord_guilds.services import CreateGuild

    logger.info("Logged in as %s, id: %s", client.user.name, client.user.id)

    # Get all users on the server
    async for guild in client.fetch_guilds():
        guild = client.get_guild(guild.id)
        for user in guild.members:
            # Create an object for each member
            member = guild.get_member(user.id)
            print(member, member.id, user.id)
            # Todo: make sure username wasn't changed
            await sync_to_async(CreateMember.execute)(
                {
                    "discord_id": member.id,
                    "discord_name": member.name,
                }
            )

        await sync_to_async(CreateGuild.execute)(
            {
                "discord_id": guild.id,
            }
        )

        print(guild.roles)


@sync_to_async
def run_tasks_sync(client):
    from tasks.models import Task
    from responses.models import Response
    from bot.users.models import Member
    from team.models import Team
    from player.models import Player
    from tasks.models import TaskType
    from bot.discord_roles.models import Role

    # Currently set up to run just message tasks
    task_list = Task.objects.filter(completed=False)
    for task in task_list:
        if task.task_type == TaskType.MESSAGE:
            player_id = task.payload["player_id"]
            message = task.payload["message"]

            player = Player.objects.get(id=player_id)

            discord_user = async_to_sync(client.fetch_user)(
                player.discord_member.discord_id
            )
            discord_message = async_to_sync(discord_user.send)(message)

            response = Response.objects.create(question_id=discord_message.id)
            player.responses.add(response)
            player.save()

        elif task.task_type == TaskType.CHANGE_TEAM:
            player_id = task.payload["player_id"]
            new_team_id = task.payload["new_team_id"]

            player = Player.objects.get(id=player_id)
            team = Team.objects.get(id=new_team_id)

            guild = client.get_guild(player.guild.discord_id)

            # TODO: Try to change this to get_member
            discord_member = async_to_sync(guild.fetch_member)(
                player.discord_member.discord_id
            )

            teams = [team for team in Team.objects.all()]
            team_names = [team.name for team in teams]

            # raise Exception([guild.get_role(team.role.discord_id) for team in teams])

            # Will remove all roles from the player
            async_to_sync(discord_member.remove_roles)(
                *[guild.get_role(team.role.discord_id) for team in teams]
            )

            # Add the new team role
            async_to_sync(discord_member.add_roles)(guild.get_role(team.role.discord_id))

        elif task.task_type == TaskType.ADD_ROLE:
            team_id = task.payload["team_id"]

            team = Team.objects.get(id=team_id)

            roles = client.get_guild(team.guild.discord_id).roles
            role_dict = {}
            for role in roles:
                role_dict[role.name] = role

            role_names = [role.name for role in roles]

            # Check if the team is already in the guild
            if team.name in role_names:
                async_to_sync(role_dict[team.name].delete)()

            # Create a role for the team
            role_object = async_to_sync(
                client.get_guild(team.guild.discord_id).create_role
            )(name=team.name, hoist=True, mentionable=True, colour=discord.Colour.red())

            new_role, _ = Role.objects.get_or_create(discord_id=role_object.id)

            team.role = new_role
            team.save()

        else:
            # TASK ERROR
            print("Error with task")

        task.completed = True
        task.save()


# Todo: better way to periodically run tasks
async def run_tasks(client):
    from tasks.models import Task

    while True:
        await asyncio.sleep(1)
        await run_tasks_sync(client)


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
    django.setup()  # configures logging etc.
    logger.info("Starting up bot")

    pool = MethodPool()  # pool that holds all callbacks
    event_pool = EventPool()
    for plugin, options in settings.PLUGINS.items():
        if not options.get("enabled", True):
            continue

        module = plugin

        if module in settings.INSTALLED_APPS:
            module = "%s.plugin" % module

        _plugin = import_module(module)
        plugin = _plugin.Plugin(client, options)
        pool.register(plugin)
        event_pool.register(plugin)
        logger.debug("Configured plugin %r", plugin)

    # bind the callback pool
    pool.bind_to(client)

    client.loop.create_task(run_tasks(client))

    # login & start
    client.run(settings.TOKEN)
