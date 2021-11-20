import logging
from asyncio import Task

import discord
from asgiref.sync import async_to_sync, sync_to_async

from bot.discord_models.models import Channel, Role
from bot.services.TaskHandler import TaskHandler
from currencies.models import Trade
from currencies.services import CreateTradeEmbed
from django import views
from teams.models import Team

from .utils import create_button_view

logger = logging.getLogger("bot")


class TradeView:
    trade: Trade = None
    interaction: discord.Interaction = None
    handler: TaskHandler = None
    client: discord.Client = None

    party: Team = None
    other_party: Team = None

    party_discord_role: discord.Role
    other_party_discord_role: discord.Role

    def __init__(self, trade, interaction, handler, client):
        self.trade: Trade = trade
        self.interaction: discord.Interaction = interaction
        self.handler: TaskHandler = handler
        self.client: discord.Client = client

        # Alternate the main team
        if trade.state == "initiating_party_view":
            self.party = self.trade.initiating_party
            self.other_party = self.trade.receiving_party

            self.party_embed = self.trade.initiating_embed_id
            self.other_party_embed = self.trade.receiving_embed_id

            self.party_thread = self.trade.initiating_party_discord_trade_thread
            self.other_party_thread = self.trade.receiving_party_discord_trade_thread

        elif trade.state == "receiving_party_view":
            self.party = self.trade.receiving_party
            self.other_party = self.trade.initiating_party

            self.party_embed = self.trade.receiving_embed_id
            self.other_party_embed = self.trade.initiating_embed_id

            self.party_thread = self.trade.receiving_party_discord_trade_thread
            self.other_party_thread = self.trade.initiating_party_discord_trade_thread

        self.party_discord_role: discord.Role = self.interaction.guild.get_role(
            self.party.role.discord_id
        )

        if self.party_discord_role is None:
            async_to_sync(self.interaction.response.send_message)(
                content="Could not find current party role",
                ephemeral=True,
            )

            return

        self.other_party_discord_role: discord.Role = self.interaction.guild.get_role(
            self.other_party.role.discord_id
        )

        if self.other_party_discord_role is None:
            async_to_sync(interaction.response.send_message)(
                content="Could not find other party role",
                ephemeral=True,
            )

            return

    def active_trade_buttons(self):
        from .Button import Button

        button_rows = [
            [
                {
                    "x": 0,
                    "y": 0,
                    "style": discord.ButtonStyle.primary,
                    "disabled": False,
                    "label": "Adjust trade amounts",
                    "custom_id": f"{self.trade.id}",
                    "emoji": "✏️",
                    "do_next": Button.currency_trade_adjustment_menu.__name__,
                    "callback_payload": {
                        "trade_id": self.trade.id,
                        "team_id": self.party.id,
                    },
                }
            ]
        ]

        if (
            self.trade.initiating_party_accepted == False
            and self.trade.receiving_party_accepted == False
        ):
            button_rows[0].append(
                {
                    "x": 0,
                    "y": 1,
                    "style": discord.ButtonStyle.success,
                    "disabled": False,
                    "label": f"Send to {self.other_party.name}",
                    "emoji": "✅",
                    "do_next": Button.accept_trade.__name__,
                    "callback_payload": {"trade_id": self.trade.id},
                },
            )
        elif (
            self.trade.initiating_party_accepted == True
            and self.trade.receiving_party_accepted == False
        ):
            button_rows[0].append(
                {
                    "x": 0,
                    "y": 1,
                    "style": discord.ButtonStyle.success,
                    "disabled": False,
                    "label": f"Return to {self.other_party.name}",
                    "emoji": "✅",
                    "do_next": Button.accept_trade.__name__,
                    "callback_payload": {"trade_id": self.trade.id},
                },
            )
        elif (
            self.trade.initiating_party_accepted == True
            and self.trade.receiving_party_accepted == True
        ):
            button_rows[0].append(
                {
                    "x": 0,
                    "y": 1,
                    "style": discord.ButtonStyle.primary,
                    "disabled": False,
                    "label": "Lock in trade",
                    "emoji": "🔒",
                    "do_next": Button.lock_in_trade.__name__,
                    "callback_payload": {"trade_id": self.trade.id},
                },
            )
        else:
            logger.debug("Trade not in correct state")

        button_rows[0].append(
            {
                "x": 1,
                "y": 1,
                "style": discord.ButtonStyle.danger,
                "disabled": False,
                "label": "Cancel trade",
                "emoji": "❌",
                "do_next": "cancel_trade",
                "callback_payload": {"trade_id": self.trade.id},
            }
        )
        self.trade.save()

        return button_rows

    def waiting_trade_buttons(self):
        from .Button import Button

        button_rows = [
            [
                {
                    "x": 0,
                    "y": 0,
                    "style": discord.ButtonStyle.danger,
                    "disabled": False,
                    "label": "Cancel Trade",
                    "custom_id": f"{self.trade.id}",
                    "emoji": "❌",
                    "do_next": Button.currency_trade_adjustment_menu.__name__,
                    "callback_payload": {
                        "trade_id": self.trade.id,
                        "team_id": self.party.id,
                    },
                }
            ]
        ]

        return button_rows

    def create_trade_view(self):
        # overwrites = {
        #     self.everyone_role: discord.PermissionOverwrite(send_messages=False),
        # }

        # Create initiating team thread
        thread_name = f"Trade with {self.other_party.name}"
        initiating_trade_thread = async_to_sync(self.handler.create_thread)(
            {
                "channel_id": self.party.trade_channel.id,  # initiating party trade channel
                "message": f"{self.party_discord_role.mention}, your trade with {self.other_party.name} has been created",  # ping that team
                "name": thread_name,  # trade with other team
            }
        )

        # Create initiating channel for trade
        (
            self.trade.initiating_party_discord_trade_thread,
            _,
        ) = Channel.objects.get_or_create(
            discord_id=initiating_trade_thread.id,
            guild=self.trade.discord_guild,
            name=initiating_trade_thread.name,
        )

        button_rows = self.active_trade_buttons()

        initiating_button = async_to_sync(self.handler.create_button)(
            {
                "guild_id": self.interaction.guild.id,
                "channel_discord_id": self.trade.initiating_party_discord_trade_thread.discord_id,
                "trade_id": self.trade.id,
                "callback_payload": {},
                "button_rows": button_rows,
            },
        )
        self.trade.initiating_embed_id = initiating_button.id

        # Create receiving team thread
        thread_name = f"Trade with {self.party.name}"
        receiving_trade_thread = async_to_sync(self.handler.create_thread)(
            {
                "channel_id": self.other_party.trade_channel.id,  # receiving party trade channel
                "message": f"{self.other_party_discord_role.mention}, your trade with {self.party.name} has been created",  # ping that team
                "name": thread_name,  # trade with other team
            }
        )

        # Create receiving channel for trade
        (
            self.trade.receiving_party_discord_trade_thread,
            _,
        ) = Channel.objects.get_or_create(
            discord_id=receiving_trade_thread.id,
            guild=self.trade.discord_guild,
            name=receiving_trade_thread.name,
        )

        button_rows = self.waiting_trade_buttons()

        receiving_button = async_to_sync(self.handler.create_button)(
            {
                "guild_id": self.interaction.guild.id,
                "channel_discord_id": self.trade.receiving_party_discord_trade_thread.discord_id,
                "callback_payload": {},
                "button_rows": button_rows,
                "content": f"Waiting for {self.other_party.name} to accept trade",
            },
        )
        self.trade.receiving_embed_id = receiving_button.id

        self.trade.save()

    def update_trade_view(self):
        # Current party
        current_party_discord_channel = self.client.get_channel(
            self.party_thread.discord_id
        )
        current_party_message: discord.Message = async_to_sync(
            current_party_discord_channel.fetch_message
        )(self.party_embed)
        current_updated_view = async_to_sync(create_button_view)(
            self.client, self.active_trade_buttons()
        )
        print(current_updated_view)
        print(current_party_message)
        async_to_sync(current_party_message.edit)(view=current_updated_view)

        # Other party
        receiving_channel = self.client.get_channel(self.other_party_thread.discord_id)
        receiving_message: discord.Message = async_to_sync(
            receiving_channel.fetch_message
        )(self.other_party_embed)
        receiving_updated_view = async_to_sync(create_button_view)(
            self.client, self.waiting_trade_buttons()
        )
        print(receiving_updated_view)
        print(receiving_message)
        async_to_sync(receiving_message.edit)(view=receiving_updated_view)

    # elif trade.state == "initiating_party_accepted":
    #     interacting_team: Team = trade.initiating_party

    #     # delete that channel
    #     # create second thread for other team

    #     if interacting_team.id == trade.initiating_party.id:
    #         trade.initiating_party_accepted = not trade.initiating_party_accepted
    #     elif interacting_team.id == trade.receiving_party.id:
    #         trade.receiving_party_accepted = not trade.receiving_party_accepted

    #     await sync_to_async(trade.save)()

    #     embed = await sync_to_async(CreateTradeEmbed.execute)({"trade_id": trade_id})

    #     message: discord.Message = await interaction.channel.fetch_message(
    #         trade.embed_id
    #     )

    #     view = await trade_view(self.client, trade)

    #     await message.edit(embed=embed, view=view)
