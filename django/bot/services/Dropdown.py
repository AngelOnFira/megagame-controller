import logging
from typing import Tuple

import discord
import emojis
from asgiref.sync import sync_to_async
from bot.discord_models.models import Category, Channel, Guild, Role
from bot.users.models import Member
from currencies.models import Currency, Trade
from currencies.services import CreateBankEmbed, CreateTradeEmbed
from players.models import Player
from responses.models import Response
from teams.models import Team

from .TaskHandler import TaskHandler

logger = logging.getLogger("bot")


class Dropdown(discord.ui.Select):
    def __init__(self, client, options, do_next, callback_payload: dict):
        super().__init__(**options)

        if client is None:
            logger.error("Dropdown: client is None")
            return

        self.client: discord.Client = client

        self.do_next = do_next
        self.callback_payload = callback_payload

    async def callback(self, interaction: discord.Interaction):
        async def trade_country_chosen(interaction: discord.Interaction):
            trade_category = list(
                filter(
                    lambda x: x.name.lower() == "trades", interaction.guild.categories
                )
            )

            if len(trade_category) > 1:
                logger.warning("There is more than one trade category!")

            trade_id = self.callback_payload["trade_id"]

            trade: Trade = await sync_to_async(Trade.objects.get)(id=trade_id)

            receiving_team_id = trade.team_lookup[self.values[0]]

            trade.receiving_party = await sync_to_async(Team.objects.get)(
                id=receiving_team_id
            )

            await sync_to_async(trade.save)()

            @sync_to_async
            def get_involved_teams(
                trade: Trade,
            ) -> Tuple[Team, Role, Channel, Team, Role, Channel, Guild]:
                if trade.initiating_party is None:
                    logger.error("Trade has no initiating party!")
                if trade.receiving_party is None:
                    logger.error("Trade has no receiving party!")

                return (
                    trade.initiating_party,
                    trade.initiating_party.role,
                    trade.initiating_party.trade_channel,
                    trade.receiving_party,
                    trade.receiving_party.role,
                    trade.receiving_party.trade_channel,
                    trade.discord_guild,
                )

            (
                initiating_party,
                initiating_party_role,
                initiating_party_trade_channel,
                receiving_party,
                receiving_party_role,
                receiving_party_trade_channel,
                discord_guild,
            ) = await get_involved_teams(trade)

            everyone_role = interaction.guild.default_role
            initiating_party_role = interaction.guild.get_role(
                initiating_party_role.discord_id
            )

            if initiating_party_role is None:
                await interaction.response.send_message(
                    content="Could not find initiating party role",
                    ephemeral=True,
                )

                return

            receiving_party_role = interaction.guild.get_role(
                receiving_party_role.discord_id
            )

            if receiving_party_role is None:
                await interaction.response.send_message(
                    content="Could not find receiving party role",
                    ephemeral=True,
                )

                return

            overwrites = {
                everyone_role: discord.PermissionOverwrite(view_channel=False),
                initiating_party_role: discord.PermissionOverwrite(view_channel=True),
                receiving_party_role: discord.PermissionOverwrite(view_channel=True),
            }

            # Create handler to call creation methods directly
            handler = TaskHandler(
                view=discord.ui.View(timeout=None), client=self.client
            )

            # Create the threads
            initiating_thread_name = f"Trade with {receiving_party.name}"
            initiating_party_trade_thread = await handler.create_thread(
                {
                    "channel_id": initiating_party_trade_channel.id,  # initiating party trade channel
                    "message": f"{initiating_party_role.mention}, your trade with {receiving_party.name} has been created",  # ping that team
                    "name": initiating_thread_name,  # trade with other team
                }
            )

            # create channel for trade
            trade.initiating_party_discord_thread, _ = await sync_to_async(
                Channel.objects.get_or_create
            )(
                discord_id=initiating_party_trade_thread.id,
                guild=discord_guild,
                name=initiating_party_trade_thread.name,
            )

            receiving_thread_name = f"Trade with {initiating_party.name}"
            receiving_party_trade_thread = await handler.create_thread(
                {
                    "channel_id": receiving_party_trade_channel.id,
                    "message": f"{receiving_party_role.mention} a trade for you has been created by {initiating_party.name}",
                    "name": receiving_thread_name,
                }
            )

            trade.receiving_party_discord_thread, _ = await sync_to_async(
                Channel.objects.get_or_create
            )(
                discord_id=receiving_party_trade_thread.id,
                guild=discord_guild,
                name=receiving_party_trade_thread.name,
            )

            # Reply in old channel with link to the trade
            await interaction.response.send_message(
                content=f"Trade channel created! You can access it here: {initiating_party_trade_thread.mention}",
                ephemeral=True,
            )

            button_messsage = await handler.create_button(
                {
                    "guild_id": interaction.guild.id,
                    "trade_id": trade_id,
                    "channel_id": initiating_party_trade_thread.id,
                    "callback_payload": {},
                    "button_rows": [
                        [
                            {
                                "x": 0,
                                "y": 0,
                                "style": discord.ButtonStyle.primary,
                                "disabled": False,
                                "label": "Adjust trade amounts",
                                "custom_id": f"{trade.id}",
                                "emoji": "✏️",
                                "do_next": "currency_trade_adjustment_menu",
                                "callback_payload": {"trade_id": trade.id},
                            },
                            # {
                            #     "x": 0,
                            #     "y": 1,
                            #     "style": discord.ButtonStyle.danger,
                            #     "disabled": False,
                            #     "label": "Cancel trade",
                            #     "emoji": "❌",
                            #     "do_next": "cancel_trade",
                            #     "callback_payload": {"trade_id": trade.id},
                            # },
                            {
                                "x": 1,
                                "y": 1,
                                "style": discord.ButtonStyle.success,
                                "disabled": False,
                                "label": "Toggle Trade Accept",
                                "emoji": "✅",
                                "do_next": "accept_trade",
                                "callback_payload": {"trade_id": trade.id},
                            },
                            {
                                "x": 2,
                                "y": 1,
                                "style": discord.ButtonStyle.primary,
                                "disabled": True,
                                "label": "Lock in trade",
                                "emoji": "🔒",
                                "do_next": "lock_in_trade",
                                "callback_payload": {"trade_id": trade.id},
                            },
                        ]
                    ],
                },
            )

            button_messsage = await handler.create_button(
                {
                    "guild_id": interaction.guild.id,
                    "trade_id": trade_id,
                    "channel_id": receiving_party_trade_thread.id,
                    "callback_payload": {},
                    "button_rows": [
                        [
                            {
                                "x": 0,
                                "y": 0,
                                "style": discord.ButtonStyle.primary,
                                "disabled": False,
                                "label": "Adjust trade amounts",
                                "custom_id": f"{trade.id}",
                                "emoji": "✏️",
                                "do_next": "currency_trade_adjustment_menu",
                                "callback_payload": {"trade_id": trade.id},
                            },
                            # {
                            #     "x": 0,
                            #     "y": 1,
                            #     "style": discord.ButtonStyle.danger,
                            #     "disabled": False,
                            #     "label": "Cancel trade",
                            #     "emoji": "❌",
                            #     "do_next": "cancel_trade",
                            #     "callback_payload": {"trade_id": trade.id},
                            # },
                            {
                                "x": 1,
                                "y": 1,
                                "style": discord.ButtonStyle.success,
                                "disabled": False,
                                "label": "Toggle Trade Accept",
                                "emoji": "✅",
                                "do_next": "accept_trade",
                                "callback_payload": {"trade_id": trade.id},
                            },
                            {
                                "x": 2,
                                "y": 1,
                                "style": discord.ButtonStyle.primary,
                                "disabled": True,
                                "label": "Lock in trade",
                                "emoji": "🔒",
                                "do_next": "lock_in_trade",
                                "callback_payload": {"trade_id": trade.id},
                            },
                        ]
                    ],
                },
            )

            trade.embed_id = button_messsage.id

            await sync_to_async(trade.save)()

        async def adjustment_select_trade_currency(interaction: discord.Interaction):
            # get currency by name
            # replace this embed with buttons
            currency_name = self.values[0]

            from .Button import Button

            currency: Currency = await sync_to_async(Currency.objects.get)(
                name=currency_name
            )

            view = discord.ui.View(timeout=None)

            for j, label in enumerate(["-5", "-1", "+1", "+5"]):
                style = (
                    discord.ButtonStyle.danger if j < 2 else discord.ButtonStyle.success
                )

                button = Button(
                    self.client,
                    j,
                    0,
                    {
                        "style": style,
                        "label": label,
                        "row": 1,
                    },
                    do_next="adjust_currency_trade",
                    callback_payload={
                        "trade_id": self.callback_payload["trade_id"],
                        "currency_id": currency.id,
                        "amount": int(label),
                    },
                )

                view.add_item(button)

            currency_button = Button(
                self.client,
                4,
                0,
                {
                    "style": discord.ButtonStyle.primary,
                    "label": currency.name,
                    "row": 1,
                    "emoji": emojis.encode(currency.emoji),
                    "disabled": True,
                },
                do_next="unreachable",
                callback_payload={},
            )

            view.add_item(currency_button)

            await interaction.response.send_message(
                view=view,
                content=f"Adjust how many {currency.name} you will send.",
                ephemeral=True,
            )

        function_lookup = {
            "trade_country_chosen": trade_country_chosen,
            "adjustment_select_trade_currency": adjustment_select_trade_currency,
        }

        await function_lookup[self.do_next](interaction)
