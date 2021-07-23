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

logger = logging.getLogger("bot")

client = discord.Client()


@client.event
async def on_ready():
    logger.info("Logged in as %s, id: %s", client.user.name, client.user.id)


from asgiref.sync import sync_to_async, async_to_sync


@sync_to_async
def run_tasks_sync(client):
    from tasks.models import Task

    print("Running tasks")
    task_list = Task.objects.filter(completed=False)
    for task in task_list:
        user = async_to_sync(client.fetch_user)(task.player.discord_member.discord_id)
        async_to_sync(user.send)(task.description)
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
