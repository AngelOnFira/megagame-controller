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
import sys
import time
from distutils.log import debug, info
from importlib import import_module
from json import JSONDecoder

import discord
import emojis
import requests
import sentry_sdk
from aiohttp import payload
from asgiref.sync import async_to_sync, sync_to_async
from discord.ext import tasks
from discord_sentry_reporting import use_sentry

import django
from bot.plugins.base import MethodPool
from bot.plugins.events import EventPool
from django.apps import AppConfig
from django.conf import settings

logger = logging.getLogger("bot")

intents = discord.Intents.default()
intents.members = True

client = discord.Client(intents=intents)

PAYMENT = "payment"
TURN = "turn"
ADJUST_CURRENCY = "adjust"

# TODO: Add this to env vars
use_sentry(
    client,
    dsn="https://b5254996d45d4a10af15a459c4ee8db4@o979577.ingest.sentry.io/5934630",
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=1.0,
)


@client.event
async def on_ready():
    logger.info("Logged in as %s, id: %s", client.user.name, client.user.id)

    await add_test_commands()

    background_task.start()


async def run_tasks_sync(client: discord.Client):
    # Need to import here to not cause circular imports
    from bot.services.TaskHandler import TaskHandler
    from tasks.models import Task, TaskType

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

        elif task.task_type == TaskType.CREATE_TEAM_CHANNEL:
            await handler.create_team_channel(payload)

        elif task.task_type == TaskType.CREATE_TEAM_VOICE_CHANNEL:
            await handler.create_team_voice_channel(payload)

        elif task.task_type == TaskType.CREATE_CATEGORY_CHANNEL:
            await handler.create_category_channel(payload)

        # elif task.task_type == TaskType.CREATE_DROPDOWN:
        #     await handler.create_dropdown(payload)

        elif task.task_type == TaskType.CREATE_BUTTONS:
            await handler.create_button(payload)

        elif task.task_type == TaskType.CREATE_MESSAGE:
            await handler.create_message(payload)

        elif task.task_type == TaskType.CREATE_THREAD:
            await handler.create_thread(payload)

        else:
            # TASK ERROR
            logger.error(f"Error with task: {task.task_type}, payload: {payload}")

        task.completed = True
        await sync_to_async(task.save)()


@client.event
async def on_interaction(interaction: discord.Interaction):
    from bot.services.Payment import create_payment_view
    from bot.services.TaskHandler import TaskHandler
    from currencies.models import Payment

    if interaction.type == discord.InteractionType.application_command:
        data = interaction.data

        data_dict = {item["name"]: item["value"] for item in data["options"]}

        # Verify that user is admin (should already be verified by discord)
        if "admin" not in [role.name for role in interaction.user.roles]:
            await interaction.response.send_message(
                "❗ You are not an admin.",
                ephemeral=True,
            )
            return

        if data["name"] == PAYMENT:
            if "cost" not in data_dict:
                cost = 1
            else:
                cost = data_dict["cost"]

            # Make sure amount is greater than 0
            if cost == 0:
                await interaction.response.send_message(
                    content="Cost must be greater than 0", ephemeral=True
                )
                return

            payment = await sync_to_async(Payment.objects.create)(
                action=data_dict["action"],
                cost=cost,
                channel_id=interaction.channel.id,
            )

            handler = TaskHandler(discord.ui.View(timeout=None), client)
            await sync_to_async(create_payment_view)(handler, payment, interaction)

        elif data["name"] == TURN:
            info("Turn: {}".format(data_dict["turn"]))
            # TODO: send announcement

            from teams.models import Team
            from teams.services import GlobalTurnChange

            advance = True

            if data_dict["turn"] == "turn_back":
                advance = False

            await sync_to_async(GlobalTurnChange.execute)(
                {
                    "advance": advance,
                }
            )

            teams = await sync_to_async(list)(Team.objects.all())
            for team in teams:
                if team.name == "null":
                    continue

                await sync_to_async(team.update_bank_embed)(client)

            if advance:
                await interaction.response.send_message(
                    content="Advancing a turn", ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    content="Going back a turn", ephemeral=True
                )

        elif data["name"] == ADJUST_CURRENCY:
            from currencies.services import CreateCompletedTransaction
            from teams.models import Team

            if "currency" not in data_dict and "currency_custom" not in data_dict:
                await interaction.response.send_message(
                    content="Please specify a currency", ephemeral=True
                )
                return

            if "currency" in data_dict and "currency_custom" in data_dict:
                await interaction.response.send_message(
                    content="Please specify only one currency", ephemeral=True
                )
                return

            response = await sync_to_async(CreateCompletedTransaction.execute)(
                {
                    "team_name": data_dict["team"],
                    "currency_name": data_dict["currency"]
                    if "currency" in data_dict
                    else data_dict["currency_custom"],
                    "amount": data_dict["amount"],
                }
            )

            team = await sync_to_async(Team.objects.get)(name=data_dict["team"])
            await sync_to_async(team.update_bank_embed)(client)

            await interaction.response.send_message(content=response, ephemeral=True)


# Check for new tasks once a second
@tasks.loop(seconds=1.0)
async def background_task():
    await run_tasks_sync(client)


@sync_to_async
def add_test_commands():
    pass


@background_task.before_loop
async def before_my_task():
    await client.wait_until_ready()  # wait until the bot logs in

    from bot.discord_models.models import Category, Channel, Guild, Role
    from bot.discord_models.services import CreateGuild
    from bot.services.TaskHandler import TEAM_ROLE_COLOUR
    from bot.state import intial_state_check
    from bot.users.services import CreateMember
    from tasks.models import TaskType
    from tasks.services import QueueTask
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

        logger.debug("Deleting channels that aren't in the database...")
        channels_stored: list[Channel] = await sync_to_async(list)(
            Channel.objects.all()
        )
        channel_ids = [channel.discord_id for channel in channels_stored]
        for channel in guild.channels:
            if (
                not channel.name.startswith("test-")
                and (
                    isinstance(channel, discord.TextChannel)
                    or isinstance(channel, discord.VoiceChannel)
                )
                and channel.id not in channel_ids
            ):
                await channel.delete()

        logger.debug("Deleting categories that aren't in the database...")
        categories_stored = await sync_to_async(list)(Category.objects.all())
        category_ids = [category.discord_id for category in categories_stored]
        for category in guild.categories:
            if not category.name.startswith("dev-") and category.id not in category_ids:
                await category.delete()

        logger.debug("Deleting roles that aren't in the database...")
        roles_stored = await sync_to_async(list)(Role.objects.all())
        for role in guild.roles:
            if role.colour == TEAM_ROLE_COLOUR and role.id not in roles_stored:
                await role.delete()
        logger.debug("Done preparing...")

        # Go through each team and remake their embeds
        # TODO: get this to delete old messages
        teams = await sync_to_async(list)(Team.objects.all())

        # TODO: create test channel to print all emojis of teams, currencies, and so on

        # for team in teams:
        #     team = await sync_to_async(Team.objects.get)(id=team.id)
        #     if team.name == "null":
        #         continue

        #     @sync_to_async
        #     def get_team(team):
        #         return team.guild, team.menu_channel

        #     team_guild, team_menu_channel = await get_team(team)

        #     guild = client.get_guild(team_guild.discord_id)

        #     # Add bank message
        #     await sync_to_async(QueueTask.execute)(
        #         {
        #             "task_type": TaskType.CREATE_MESSAGE,
        #             "payload": {
        #                 "channel_id": team_menu_channel.id,
        #                 "message": "team_bank_embed",
        #                 "team_id": team.id,
        #             },
        #         }
        #     )

        #     button_rows = [
        #         [
        #             {
        #                 "x": 0,
        #                 "y": 0,
        #                 "style": discord.ButtonStyle.primary,
        #                 "disabled": False,
        #                 "label": "Start trade",
        #                 "custom_id": f"{team.id}",
        #                 "emoji": "💱",
        #                 "do_next": "start_trading",
        #                 "callback_payload": {},
        #             }
        #         ]
        #     ]

        #     # Add a buttons message as a menu
        #     await sync_to_async(QueueTask.execute)(
        #         {
        #             "task_type": TaskType.CREATE_BUTTONS,
        #             "payload": {
        #                 "team_id": team.id,
        #                 "guild_id": team_guild.discord_id,
        #                 "button_rows": button_rows,
        #                 "embed": {
        #                     "title": "Team menu",
        #                     "description": "Choose what you would like to do",
        #                     "color": 0x00FF00,
        #                 },
        #             },
        #         }
        #     )

        admin_id = list(filter(lambda x: x.name == "admin", guild.roles))[0].id

        def create_command(json, admin_id):
            application_id = "881015675236270121"
            guild_id = "855215558994821120"

            url = f"https://discord.com/api/v8/applications/{application_id}/guilds/{guild_id}/commands"
            headers = {
                "Authorization": "Bot ODgxMDE1Njc1MjM2MjcwMTIx.YSmryQ.BqFwf7vhSHrBjuA0J6F5cXkzMwg"
            }
            r = requests.post(url, headers=headers, json=json)

            text = JSONDecoder().decode(r.text)

            debug(text["id"] if "id" in text else "No id")

            # Set permissions
            url = "https://discord.com/api/v8/applications/{}/guilds/{}/commands/{}/permissions".format(
                application_id, guild_id, text["id"]
            )

            json = {"permissions": [{"id": admin_id, "type": 1, "permission": True}]}

            r = requests.put(url, headers=headers, json=json)

        # Payment command
        create_command(
            {
                "name": PAYMENT,
                "type": 1,
                "description": "Create a payment that teams can react to",
                "default_permission": False,
                "options": [
                    {
                        "name": "action",
                        "description": "The string that will be show as what players are purchsing",
                        "type": 3,
                        "required": True,
                    },
                    {
                        "name": "cost",
                        "description": "Cost of this action, in the 'common' currency",
                        "type": 4,
                        "required": False,
                    },
                ],
            },
            admin_id,
        )

        # Turn advance command
        create_command(
            {
                "name": TURN,
                "type": 1,
                "description": "Advance or go back a turn",
                "default_permission": False,
                "options": [
                    {
                        "name": "turn",
                        "description": "Go back or forward a game turn",
                        "type": 3,
                        "required": True,
                        "choices": [
                            {"name": "Advance", "value": "turn_advance"},
                            {"name": "Go back", "value": "turn_back"},
                        ],
                    },
                ],
            },
            admin_id,
        )

        teams = await sync_to_async(list)(Team.objects.all())

        team_choices = [
            {"name": team.name, "value": team.name}
            for team in teams
            if team.name != "null"
        ]

        from currencies.models import Currency

        currencies = await sync_to_async(list)(Currency.objects.all())

        currency_choices = [
            {
                "name": f"{emojis.encode(currency.emoji)} {currency.name}",
                "value": currency.name,
            }
            for currency in currencies
            if currency.currency_type in ["COM", "RAR", "LOG"]
        ]

        # Pay team command
        create_command(
            {
                "name": ADJUST_CURRENCY,
                "type": 1,
                "description": "Add or remove an amount of a currency from a team",
                "default_permission": False,
                "options": [
                    {
                        "name": "team",
                        "description": "The team to adjust",
                        "type": 3,
                        "required": True,
                        "choices": team_choices,
                    },
                    {
                        "name": "amount",
                        "description": "The amount to adjust",
                        "type": 4,
                        "required": True,
                    },
                    {
                        "name": "currency",
                        "description": "The currency to adjust",
                        "type": 3,
                        "required": False,
                        "choices": currency_choices,
                    },
                    {
                        "name": "custom_currency",
                        "description": "Adjust a non common/rare/logistics currency ",
                        "type": 3,
                        "required": False,
                    },
                ],
            },
            admin_id,
        )

    await intial_state_check(client)


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
    django.setup()  # configures logger etc.
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
