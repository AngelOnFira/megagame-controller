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
from .Trade import TradeView

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

        trade_view: TradeView = await sync_to_async(TradeView)(
            trade, interaction, handler, self.client
        )
        await sync_to_async(trade_view.create_trade_view)()

        # TODO: Fix this
        @sync_to_async
        def get_thread_id(trade: Trade):
            return trade.initiating_party_discord_trade_thread.discord_id

        # Update this copy of trade
        await sync_to_async(trade.refresh_from_db)()
        # trade = await sync_to_async(Trade.objects.get)(id=trade_id)

        thread_id = await get_thread_id(trade)
        trade_thread = interaction.guild.get_thread(thread_id)

        # Reply in old channel with link to the trade
        await interaction.response.send_message(
            content=f"Trade channel created! You can access it here: {trade_thread.mention}",
            ephemeral=True,
        )

    async def adjustment_select_trade_currency(self, interaction: discord.Interaction):
        """When a currency is selected, make a list of buttons to adjust the amount on the trade

        Args:
            interaction (discord.Interaction)

        Payload:
            trade_id
        """
        currency_name = self.values[0]

        from .Button import Button

        currency: Currency = await sync_to_async(Currency.objects.get)(
            name=currency_name
        )

        view = discord.ui.View(timeout=None)

        for j, label in enumerate(["-5", "-1", "+1", "+5"]):
            style = discord.ButtonStyle.danger if j < 2 else discord.ButtonStyle.success

            button = Button(
                client=self.client,
                x=j,
                y=0,
                options={
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
            client=self.client,
            x=4,
            y=0,
            options={
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

    async def open_comms_channel(self, interaction: discord.Interaction):
        """Open a comms channel for multiple teams

        Args:
            interaction (discord.Interaction)

        Payload:
            interacting_team
        """

        # Get the interacting team
        interacting_team_id = self.callback_payload["interacting_team"]
        interacting_team = await sync_to_async(Team.objects.get)(id=interacting_team_id)

        @sync_to_async
        def get_interacting_team_role(team: Team):
            return team.role

        interacting_team_role = await get_interacting_team_role(interacting_team)

        channel_name = f"{interacting_team.abreviation}"

        channel_message_description = f"--> <@&{interacting_team_role.discord_id}>\n"

        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(
                read_messages=False
            ),
        }

        # Add overwrite for the interacting team
        overwrites[
            interaction.guild.get_role(interacting_team_role.discord_id)
        ] = discord.PermissionOverwrite(read_messages=True)

        @sync_to_async
        def get_team(values):
            teams = list(Team.objects.filter(name__in=values))
            roles = [team.role for team in teams]

            return (teams, roles)

        teams_roles = await get_team(self.values)

        # Add overwrites for all other teams
        for team, role in zip(teams_roles[0], teams_roles[1]):
            overwrites[
                interaction.guild.get_role(role.discord_id)
            ] = discord.PermissionOverwrite(read_messages=True)

            channel_name += f"-{team.abreviation}"
            channel_message_description += f"--> <@&{role.discord_id}>\n"

        # Create channel with overrides in category
        comms_category = list(
            filter(lambda x: x.name.lower() == "comms", interaction.guild.categories)
        )

        if len(comms_category) > 1:
            logger.warning("There is more than one comms category!")

        if len(comms_category) == 0:
            logger.error("No comms category!")

            await interaction.response.send_message(
                content=f"Error creating the comms channel, could not find category",
                ephemeral=True,
            )

            return

        comms_category = comms_category[0]

        comms_channel = await interaction.guild.create_text_channel(
            name=channel_name,
            category=comms_category,
            overwrites=overwrites,
        )

        channel_embed: discord.Embed = discord.Embed(
            title=f"This channel was opened for delegates of:",
            description=channel_message_description,
        )

        await comms_channel.send(embed=channel_embed)

    async def callback(self, interaction: discord.Interaction):
        function_lookup = {
            self.set_up_trade_prompt.__name__: self.set_up_trade_prompt,
            self.adjustment_select_trade_currency.__name__: self.adjustment_select_trade_currency,
            self.open_comms_channel.__name__: self.open_comms_channel,
        }

        await function_lookup[self.do_next](interaction)
