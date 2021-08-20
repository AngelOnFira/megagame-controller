import logging
import emojis
import dice
import discord
import asyncio

from asgiref.sync import sync_to_async
from bot.plugins.base import BasePlugin
from team.models import Team
from tasks.services import QueueTask
from tasks.models import Task, TaskType

from .services import CreateTrade, UpdateTransaction
import json

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

            transaction = await sync_to_async(CreateTrade.execute)(
                {
                    "message_sender_id": message.author.id,
                    "team_lookup": team_lookup,
                }
            )

            await sync_to_async(QueueTask.execute)(
                {
                    "task_type": TaskType.CREATE_DROPDOWN,
                    "payload": {
                        "guild_id": message.guild.id,
                        "channel_id": message.channel.id,
                        "do_next": {
                            "type": TaskType.CREATE_TRANSACTION,
                            "team_lookup": team_lookup,
                            "transaction_id": transaction.id,
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

    async def on_reaction_add(self, reaction, user):
        # TODO (foan): reactions aren't capturing after a server restart

        # If the reaction is from the bot, ignore it
        if user.bot:
            return

        (response, emoji_lookup) = await sync_to_async(UpdateTransaction.execute)(
            {
                "message_id": reaction.message.id,
                "reaction_emoji": emojis.decode(reaction.emoji),
            }
        )

        if response == emoji_lookup == None:
            return

        if response != None:
            await reaction.message.edit(content=response)

        await reaction.message.clear_reactions()

        if emoji_lookup != None:
            for emoji in emoji_lookup.keys():
                await reaction.message.add_reaction(emojis.encode(emoji))

        return await super().on_reaction_add(reaction, user)
