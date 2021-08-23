import asyncio
import json
import logging

import dice
import discord
import emojis
from asgiref.sync import sync_to_async

from bot.discord_models.models import Channel, Guild
from bot.plugins.base import BasePlugin
from currencies.models import Currency
from tasks.models import Task, TaskType
from tasks.services import QueueTask
from teams.models import Team

from .services import CreateTrade, SelectTradeReceiver

logger = logging.getLogger(__name__)


class Dropdown(discord.ui.Select):
    async def callback(self, interaction: discord.Interaction):
        await self.callback_function(self, interaction)

    def __init__(self, options, callback):
        super().__init__(**options)
        self.callback_function = callback


class Plugin(BasePlugin):
    async def on_message(self, message):
        if message.content.startswith("!roll"):
            await message.reply(sum(dice.roll(message.content.split(" ")[1])))

        if message.content.startswith("!sys"):
            teams = await sync_to_async(list)(Team.objects.all())

            options = []
            team_lookup = {}

            for team in teams:
                if not team.emoji:
                    continue

                options.append(
                    {
                        "label": team.name,
                        "description": "",
                        "emoji": emojis.encode(team.emoji),
                    }
                )

                team_lookup[team.name] = team.id

            trade = await sync_to_async(CreateTrade.execute)(
                {
                    "message_sender_id": message.author.id,
                    "team_lookup": team_lookup,
                }
            )

            discord_channel, _ = await sync_to_async(Channel.objects.get_or_create)(
                discord_id=message.channel.id
            )
            discord_guild, _ = await sync_to_async(Guild.objects.get_or_create)(
                message.guild.id
            )

            trade.discord_channel = discord_channel
            trade.discord_guild = discord_guild

            await sync_to_async(trade.create)()
            await sync_to_async(trade.save)()

            await sync_to_async(QueueTask.execute)(
                {
                    "task_type": TaskType.CREATE_DROPDOWN,
                    "payload": {
                        "guild_id": message.guild.id,
                        "channel_id": message.channel.id,
                        "do_next": {
                            "type": TaskType.TRADE_SELECT_RECEIVER,
                            "payload": {
                                "trade_id": trade.id,
                            },
                        },
                        "dropdown": {
                            "placeholder": "Which country do you want to trade with?",
                            "min_values": 1,
                            "max_values": 1,
                            "options": options,
                        },
                    },
                }
            )
