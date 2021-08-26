#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Main entry point for the bot.

This module performs the start-up, login and reads out the settings to configure
the bot.
"""
import asyncio
import logging
import os
import time
from importlib import import_module

import discord
import emojis
from aiohttp import payload
from asgiref.sync import async_to_sync, sync_to_async
from discord.ext import tasks

import django
from bot.plugins.base import MethodPool
from bot.plugins.events import EventPool
from django.apps import AppConfig
from django.conf import settings

logger = logging.getLogger("bot")

intents = discord.Intents.default()
intents.members = True

client = discord.Client(intents=intents)

TEAM_ROLE_COLOUR = discord.Colour.red()


@client.event
async def on_ready():
    logger.info("Logged in as %s, id: %s", client.user.name, client.user.id)

    background_task.start()


async def run_tasks_sync(client: discord.Client):
    from bot.discord_models.models import Category, Channel, Role
    from bot.services import Button, Dropdown, TaskHandler, build_trade_buttons
    from bot.users.models import Member
    from currencies.models import Trade
    from currencies.services import CreateTrade, CreateTradeEmbed, SelectTradeReceiver
    from players.models import Player
    from responses.models import Response
    from tasks.models import Task, TaskType
    from teams.models import Team

    # Get all tasks that need to still be completed
    task_list = await sync_to_async(list)(Task.objects.filter(completed=False))

    for task in task_list:
        print(task.task_type)
        handler = TaskHandler(view=discord.ui.View(), client=client)
        payload: dict = task.payload

        if task.task_type == TaskType.MESSAGE:
            player_id = payload["player_id"]
            message = payload["message"]

            player = await sync_to_async(Player.objects.get)(id=player_id)

            discord_user: discord.User = await client.fetch_user(
                player.discord_member.discord_id
            )
            discord_message: discord.Message = await discord_user.send(message)

            @sync_to_async
            def update_player(discord_message):
                response = Response.objects.create(question_id=discord_message.id)
                player.responses.add(response)
                player.save()

            await update_player(discord_message)

        # Need to convert to async
        # elif task.task_type == TaskType.CHANGE_TEAM:
        #     player_id = payload["player_id"]
        #     new_team_id = payload["new_team_id"]

        #     player = Player.objects.get(id=player_id)
        #     team = Team.objects.get(id=new_team_id)

        #     guild = client.get_guild(player.guild.discord_id)

        #     # TODO: Try to change this to get_member
        #     discord_member = async_to_sync(guild.fetch_member)(
        #         player.discord_member.discord_id
        #     )

        #     teams = [team for team in Team.objects.all()]
        #     team_names = [team.name for team in teams]

        #     # raise Exception([guild.get_role(team.role.discord_id) for team in teams])

        #     # Will remove all roles from the player
        #     async_to_sync(discord_member.remove_roles)(
        #         *[guild.get_role(team.role.discord_id) for team in teams]
        #     )

        #     # Add the new team role
        #     async_to_sync(discord_member.add_roles)(
        #         guild.get_role(team.role.discord_id)
        #     )

        elif task.task_type == TaskType.CREATE_ROLE:
            team_id = payload["team_id"]

            @sync_to_async
            def get_team(team_id):
                team = Team.objects.get(id=team_id)
                team_guild = team.guild

                return team, team_guild

            team, team_guild = await get_team(team_id)

            # TODO: Problem with resetting db and running this

            roles = client.get_guild(team_guild.discord_id).roles
            role_dict = {}
            for role in roles:
                role_dict[role.name] = role

            role_names = [role.name for role in roles]

            # Check if the team is already in the guild
            if team.name in role_names:
                await role_dict[team.name].delete()

            # Create a role for the team
            role_object = await client.get_guild(team_guild.discord_id).create_role(
                name=team.name, hoist=True, mentionable=True, colour=TEAM_ROLE_COLOUR
            )

            new_role, _ = await sync_to_async(Role.objects.get_or_create)(
                discord_id=role_object.id, name=team.name, guild=team_guild
            )

            team.role = new_role
            await sync_to_async(team.save)()

        elif task.task_type == TaskType.CREATE_CATEGORY:
            await handler.create_category(payload)

        elif task.task_type == TaskType.CREATE_CHANNEL:
            team_id = payload["team_id"]
            channel_name = payload["channel_name"]

            @sync_to_async
            def get_team(team_id):
                team = Team.objects.get(id=team_id)
                team_guild = team.guild
                team_role = team.role
                team_category = team.category

                return team, team_guild, team_role, team_category

            team, team_guild, _, team_category = await get_team(team_id)

            guild = client.get_guild(team.guild.discord_id)

            # TODO: Remove fetch needed for cache busting
            category = await guild.fetch_channel(team_category.discord_id)

            text_channel = await guild.create_text_channel(
                channel_name,
                category=category,
            )

            new_channel, _ = await sync_to_async(Channel.objects.get_or_create)(
                discord_id=text_channel.id, guild=team_guild
            )

            team.general_channel = new_channel
            await sync_to_async(team.save)()

        elif task.task_type == TaskType.CREATE_DROPDOWN:
            await handler.create_dropdown(payload)

        elif task.task_type == TaskType.CREATE_BUTTONS:
            await handler.create_button(payload)

        else:
            # TASK ERROR
            print("Error with task")

        task.completed = True
        await sync_to_async(task.save)()


# Check for new tasks once a second
@tasks.loop(seconds=1.0)
async def background_task():
    await run_tasks_sync(client)


@background_task.before_loop
async def before_my_task():
    await client.wait_until_ready()  # wait until the bot logs in

    from bot.discord_models.models import Category, Channel, Guild, Role
    from bot.discord_models.services import CreateGuild
    from bot.users.services import CreateMember
    from teams.models import Team

    # Get all users on the server
    async for guild in client.fetch_guilds():
        guild = client.get_guild(guild.id)
        await sync_to_async(CreateGuild.execute)(
            {
                "discord_id": guild.id,
            }
        )

        for user in guild.members:
            # Create an object for each member
            member = guild.get_member(user.id)
            # Todo: make sure username wasn't changed
            await sync_to_async(CreateMember.execute)(
                {
                    "discord_id": member.id,
                    "discord_name": member.name,
                }
            )

        print("Deleting channels that aren't in the database...")
        channels_stored = await sync_to_async(list)(Channel.objects.all())
        for channel in guild.channels:
            if (
                not channel.name.startswith("test-")
                and isinstance(channel, discord.TextChannel)
                and channel.id not in channels_stored
            ):
                await channel.delete()

        print("Deleting categories that aren't in the database...")
        categories_stored = await sync_to_async(list)(Category.objects.all())
        for category in guild.categories:
            if (
                not category.name.startswith("dev-")
                and category.id not in categories_stored
            ):
                await category.delete()

        print("Deleting roles that aren't in the database...")
        roles_stored = await sync_to_async(list)(Role.objects.all())
        for role in guild.roles:
            if role.colour == TEAM_ROLE_COLOUR and role.id not in roles_stored:
                await role.delete()


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

    # login & start
    client.run(settings.TOKEN)
