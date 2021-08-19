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
import emojis
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

    # Needed to prepare the cache
    # async for guild in client.fetch_guilds():
    #     guild = client.get_guild(guild.id)

    # Get all users on the server
    # async for guild in client.fetch_guilds():
    #     guild = client.get_guild(guild.id)
    #     for user in guild.members:
    #         # Create an object for each member
    #         member = guild.get_member(user.id)
    #         print(member, member.id, user.id)
    #         # Todo: make sure username wasn't changed
    #         await sync_to_async(CreateMember.execute)(
    #             {
    #                 "discord_id": member.id,
    #                 "discord_name": member.name,
    #             }
    #         )

    #     await sync_to_async(CreateGuild.execute)(
    #         {
    #             "discord_id": guild.id,
    #         }
    #     )

    #     print(guild.roles)

    background_task.start()


# @client.event
# async def on_connect():
#     background_task.start()


class Dropdown(discord.ui.Select):
    async def callback(self, interaction: discord.Interaction):
        await self.callback_function(self, interaction)

    def __init__(self, options, callback, do_next):
        super().__init__(**options)
        self.callback_function = callback
        self.do_next = do_next


@sync_to_async
def run_tasks_sync(client, view):
    from tasks.models import Task
    from responses.models import Response
    from bot.users.models import Member
    from team.models import Team
    from player.models import Player
    from tasks.models import TaskType
    from bot.discord_roles.models import Role, Category
    from currency.services import CreateTransaction, UpdateTransaction

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
            async_to_sync(discord_member.add_roles)(
                guild.get_role(team.role.discord_id)
            )

        elif task.task_type == TaskType.CREATE_ROLE:
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

        elif task.task_type == TaskType.CREATE_CATEGORY:
            team_id = task.payload["team_id"]

            team = Team.objects.get(id=team_id)

            guild = client.get_guild(team.guild.discord_id)

            if guild is None:
                raise Exception("Guild not found")

            everyone_role = guild.default_role

            team_role_id = team.role.discord_id
            team_role = guild.get_role(team_role_id)

            category_channel = async_to_sync(guild.create_category)(
                team.name,
                overwrites={
                    everyone_role: discord.PermissionOverwrite(view_channel=False),
                    team_role: discord.PermissionOverwrite(view_channel=True),
                },
            )

            team.category, _ = Category.objects.get_or_create(
                discord_id=category_channel.id
            )

            team.save()

        elif task.task_type == TaskType.CREATE_CHANNEL:
            team_id = task.payload["team_id"]
            channel_name = task.payload["channel_name"]

            team = Team.objects.get(id=team_id)

            guild = client.get_guild(team.guild.discord_id)

            # TODO: Remove fetch needed for cache busting
            category = async_to_sync(guild.fetch_channel)(team.category.discord_id)

            text_channel = async_to_sync(guild.create_text_channel)(
                channel_name,
                category=category,
            )

        elif task.task_type == TaskType.CREATE_DROPDOWN:
            guild_id = task.payload["guild_id"]
            channel_id = task.payload["channel_id"]
            dropdown = task.payload["dropdown"]
            do_next = task.payload["do_next"]

            async def callback(self: Dropdown, interaction: discord.Interaction):
                if self.do_next["type"] == TaskType.CREATE_TRANSACTION:
                    await sync_to_async(UpdateTransaction.execute)(
                        {
                            "interaction_id": interaction.id,
                            "interaction_data": interaction.message,
                            "emoji_lookup": self.do_next["emoji_lookup"],
                            "values": self.values,
                        }
                    )

            options = []

            for option in dropdown["options"]:
                options.append(discord.SelectOption(**option))

            view.add_item(
                Dropdown(
                    {
                        "placeholder": "Which country do you want to trade with?",
                        "min_values": 1,
                        "max_values": 1,
                        "options": options,
                    },
                    callback,
                    do_next=do_next,
                )
            )
            channel = client.get_guild(guild_id).get_channel(channel_id)
            async_to_sync(channel.send)("test", view=view)

        else:
            # TASK ERROR
            print("Error with task")

        task.completed = True
        task.save()


# Check for new tasks once a second
@tasks.loop(seconds=1)
async def background_task():

    # Have to create view out here as the tasks are run in sync and don't have
    # access to the event loop
    view = discord.ui.View()

    await run_tasks_sync(client, view)


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
