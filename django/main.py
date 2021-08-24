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
    from bot.discord_models.models import Category, Channel, Guild, Role
    from bot.discord_models.services import CreateGuild
    from bot.users.services import CreateMember
    from teams.models import Team

    logger.info("Logged in as %s, id: %s", client.user.name, client.user.id)

    # Get all users on the server
    async for guild in client.fetch_guilds():
        guild = client.get_guild(guild.id)
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

        await sync_to_async(CreateGuild.execute)(
            {
                "discord_id": guild.id,
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

    background_task.start()


class Dropdown(discord.ui.Select):
    async def callback(self, interaction: discord.Interaction):
        await self.callback_function(self, interaction)

    def __init__(self, options, callback, do_next):
        super().__init__(**options)
        self.callback_function = callback
        self.do_next = do_next


class Button(discord.ui.Button):
    # async def callback(self, interaction: discord.Interaction):
    #     await self.callback_function(self, interaction)

    def __init__(self, x: int, y: int, options: dict, callback=False, do_next=False):
        super().__init__(**options)
        self.x = x
        self.y = y
        # self.callback_function = callback
        # self.do_next = do_next

    async def callback(self, interaction: discord.Interaction):
        from currencies.models import Currency, Trade, Transaction
        from currencies.services import CreateTradeEmbed

        assert self.view is not None

        content = "test"

        # Get the id
        # Get a transaction model and add or remove from the currency

        currency_id, trade_id, adjustment = self.custom_id.split("|")

        currency = await sync_to_async(Currency.objects.get)(id=currency_id)

        # Have to wrap it since it needs a prefetch
        @sync_to_async
        def get_trade(trade_id):
            trade = Trade.objects.prefetch_related(
                "initiating_party", "receiving_party"
            ).get(id=trade_id)

            from_wallet = trade.initiating_party.wallet
            to_wallet = trade.receiving_party.wallet

            return trade, from_wallet, to_wallet

        trade, from_wallet, to_wallet = await get_trade(trade_id)

        transaction, _ = await sync_to_async(Transaction.objects.get_or_create)(
            trade=trade,
            currency=currency,
            defaults={
                "amount": 0,
                # TODO: Once team for button is tracked, swap this out
                "from_wallet": from_wallet,
                "to_wallet": to_wallet,
            },
        )

        adjustment_int = int(adjustment)

        transaction.amount += adjustment_int
        transaction.amount = max(transaction.amount, 0)

        if transaction.amount == 0:
            await sync_to_async(transaction.delete)()
        else:
            await sync_to_async(transaction.save)()

        # TODO: Make sure they have enough money

        embed = await sync_to_async(CreateTradeEmbed.execute)({"trade": trade})

        await interaction.response.edit_message(embed=embed, view=self.view)


@sync_to_async
def build_trade_buttons(channel_id, guild_id, trade_id):
    from currencies.models import Currency
    from tasks.models import TaskType
    from tasks.services import QueueTask

    button_rows = []

    currency: Currency
    for i, currency in enumerate(Currency.objects.all()):
        row = []

        for j, label in enumerate(["-5", "-1", "+1", "+5"]):
            style = discord.ButtonStyle.danger if j < 2 else discord.ButtonStyle.success

            # TODO: Track which team this button is associated with

            value_button = {
                "x": j,
                "y": i,
                "style": style,
                "disabled": False,
                "label": label,
                "custom_id": f"{currency.id}|{trade_id}|{label}",
            }

            row.append(value_button)

        currency_button = {
            "x": 4,
            "y": i,
            "style": discord.ButtonStyle.primary,
            "emoji": emojis.encode(currency.emoji),
            "disabled": True,
            "label": currency.name,
        }
        row.append(currency_button)

        button_rows.append(row)

    QueueTask.execute(
        {
            "task_type": TaskType.CREATE_BUTTONS,
            "payload": {
                "channel_id": channel_id,
                "guild_id": guild_id,
                "button_rows": button_rows,
                "trade_id": trade_id,
            },
        }
    )


@sync_to_async
def run_tasks_sync(client, view: discord.ui.View):
    from bot.discord_models.models import Category, Channel, Role
    from bot.users.models import Member
    from currencies.models import Trade
    from currencies.services import CreateTrade, CreateTradeEmbed, SelectTradeReceiver
    from players.models import Player
    from responses.models import Response
    from tasks.models import Task, TaskType
    from teams.models import Team

    # Currently set up to run just message tasks
    task_list = Task.objects.filter(completed=False)
    for task in task_list:
        # Reset the view
        for child in view.children:
            view.remove_item(child)

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
            )(name=team.name, hoist=True, mentionable=True, colour=TEAM_ROLE_COLOUR)

            new_role, _ = Role.objects.get_or_create(
                discord_id=role_object.id, name=team.name
            )

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

            new_channel, _ = Channel.objects.get_or_create(discord_id=text_channel.id)

            team.general_channel = new_channel
            team.save()

        elif task.task_type == TaskType.CREATE_DROPDOWN:
            guild_id = task.payload["guild_id"]
            channel_id = task.payload["channel_id"]
            dropdown = task.payload["dropdown"]
            do_next = task.payload["do_next"]

            async def callback(self: Dropdown, interaction: discord.Interaction):
                if self.do_next["type"] == TaskType.TRADE_SELECT_RECEIVER:
                    await sync_to_async(SelectTradeReceiver.execute)(
                        {
                            "payload": self.do_next["payload"],
                            "values": self.values,
                        }
                    )

                    await build_trade_buttons(
                        channel_id, guild_id, self.do_next["payload"]["trade_id"]
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

            embedVar = discord.Embed(title=" ads", description=" d", color=0x00FF00)

            async_to_sync(channel.send)(embed=embedVar, view=view)

        elif task.task_type == TaskType.CREATE_BUTTONS:
            guild_id = task.payload["guild_id"]
            button_rows = task.payload["button_rows"]

            if "channel_id" in task.payload:
                channel_id = task.payload["channel_id"]
            elif "team_id" in task.payload:
                team_id = task.payload["team_id"]
                channel_id = Team.objects.get(id=team_id).general_channel.discord_id
            else:
                raise Exception("No channel or team id found; don't know how to handle")

            channel = client.get_guild(guild_id).get_channel(channel_id)

            for row in button_rows:
                for button in row:
                    options_dict = {
                        "style": button["style"][1],
                        "label": button["label"],
                        "row": button["y"],
                    }

                    if "emoji" in button:
                        options_dict["emoji"] = button["emoji"]

                    if "disabled" in button:
                        options_dict["disabled"] = button["disabled"]

                    if "custom_id" in button:
                        options_dict["custom_id"] = button["custom_id"]

                    button = Button(
                        button["x"],
                        button["y"],
                        options_dict,
                    )

                    view.add_item(button)

                # children = view.children
                # for child in children:
                #     view.remove_item(child)

            if "trade_id" in task.payload:
                trade_id = task.payload["trade_id"]
                embed = CreateTradeEmbed.execute(
                    {"trade": Trade.objects.get(id=trade_id)}
                )
            else:
                embed = discord.Embed(
                    title="Team menu",
                    description="Choose what you would like to do",
                    color=0x00FF00,
                )

            # embedVar = discord.Embed(title="Title", description="Desc", color=0x00ff00)
            # embedVar.add_field(name="Field1", value="hi", inline=False)
            # embedVar.add_field(name="Field2", value="hi2", inline=False)

            async_to_sync(channel.send)(embed=embed, view=view)

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
