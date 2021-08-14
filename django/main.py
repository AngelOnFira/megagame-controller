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
    from player.models import Player
    from tasks.models import TaskType

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

        if task.task_type == TaskType.TEAM_CHANGE:
            pass

        if task.task_type == TaskType.ADD_ROLE:
            roles = gui

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
