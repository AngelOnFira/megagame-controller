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
import sentry_sdk
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

# TODO: Add this to env vars
sentry_sdk.init(
    "https://b5254996d45d4a10af15a459c4ee8db4@o979577.ingest.sentry.io/5934630",
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=1.0,
)


@client.event
async def on_ready():
    logger.info("Logged in as %s, id: %s", client.user.name, client.user.id)

    background_task.start()


async def run_tasks_sync(client: discord.Client):
    from bot.discord_models.models import Category, Channel, Role
    from bot.services import Button, Dropdown, TaskHandler
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
        handler = TaskHandler(view=discord.ui.View(timeout=None), client=client)
        payload: dict = task.payload

        if task.task_type == TaskType.MESSAGE:
            await handler.send_message(payload)

        elif task.task_type == TaskType.CHANGE_TEAM:
            await handler.change_team(payload)

        elif task.task_type == TaskType.CREATE_ROLE:
            await handler.create_role(payload)

        elif task.task_type == TaskType.CREATE_CATEGORY:
            await handler.create_category(payload)

        elif task.task_type == TaskType.CREATE_CHANNEL:
            await handler.create_channel(payload)

        elif task.task_type == TaskType.CREATE_DROPDOWN:
            await handler.create_dropdown(payload)

        elif task.task_type == TaskType.CREATE_BUTTONS:
            await handler.create_button(payload)

        elif task.task_type == TaskType.CREATE_MESSAGE:
            await handler.create_message(payload)

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
    from bot.services import TEAM_ROLE_COLOUR
    from bot.state import intial_state_check
    from bot.users.services import CreateMember
    from teams.models import Team

    @sync_to_async
    def get_categories():
        return list(Category.objects.all())

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

    await intial_state_check(client)


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
