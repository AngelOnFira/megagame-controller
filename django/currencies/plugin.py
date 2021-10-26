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

logger = logging.getLogger("bot")


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
