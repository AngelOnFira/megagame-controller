import logging
import time
from turtle import update
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
from .Trade import update_trade_view

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

    async def set_up_trade_prompt(self, interaction: discord.Interaction):
        # Figure out what part of the trade we are on
        #

        # trade_category = list(
        #     filter(lambda x: x.name.lower() == "trades", interaction.guild.categories)
        # )

        # if len(trade_category) > 1:
        #     logger.warning("There is more than one trade category!")

        # Get trade info

        trade_id = self.callback_payload["trade_id"]

        trade = await sync_to_async(Trade.objects.get)(id=trade_id)

        receiving_team_id = trade.team_lookup[self.values[0]]

        trade.receiving_party = await sync_to_async(Team.objects.get)(
            id=receiving_team_id
        )

        await sync_to_async(trade.save)()

        # Create handler to call creation methods directly
        handler = TaskHandler(view=discord.ui.View(timeout=None), client=self.client)

        logger.debug("Start")

        await sync_to_async(update_trade_view)(handler, trade, interaction)
        logger.debug("Done")

        @sync_to_async
        def thread_id(trade):
            return trade.current_discord_trade_thread.id

        trade_thread = interaction.guild.get_channel(await thread_id(trade))

        # Reply in old channel with link to the trade
        await interaction.response.send_message(
            content=f"Trade channel created! You can access it here: {trade_thread.mention}",
            ephemeral=True,
        )

    async def adjustment_select_trade_currency(self, interaction: discord.Interaction):
        # get currency by name
        # replace this embed with buttons
        currency_name = self.values[0]

        from .Button import Button

        currency: Currency = await sync_to_async(Currency.objects.get)(
            name=currency_name
        )

        view = discord.ui.View(timeout=None)

        for j, label in enumerate(["-5", "-1", "+1", "+5"]):
            style = discord.ButtonStyle.danger if j < 2 else discord.ButtonStyle.success

            button = Button(
                self.client,
                j,
                0,
                {
                    "style": style,
                    "label": label,
                    "row": 1,
                },
                do_next=Button.adjust_currency_trade.__name__,
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

    async def callback(self, interaction: discord.Interaction):
        function_lookup = {
            self.set_up_trade_prompt.__name__: self.set_up_trade_prompt,
            self.adjustment_select_trade_currency.__name__: self.adjustment_select_trade_currency,
        }

        await function_lookup[self.do_next](interaction)
