import discord
from asgiref.sync import async_to_sync, sync_to_async

from bot.discord_models.models import Channel
from bot.services.TaskHandler import TaskHandler
from currencies.models import Trade

# @sync_to_async
# def get_trade_info(
#     trade_id, recieving_id
# ) -> Tuple[Team, Role, Channel, Team, Role, Channel, Guild]:
#     trade: Trade = Trade.objects.get(id=trade_id)

#     if trade.initiating_party is None:
#         logger.error("Trade has no initiating party!")
#     if trade.receiving_party is None:
#         logger.error("Trade has no receiving party!")

#     return (
#         trade,
#         trade.initiating_party,
#         trade.initiating_party.role,
#         trade.initiating_party.trade_channel,
#         trade.receiving_party,
#         trade.receiving_party.role,
#         trade.receiving_party.trade_channel,
#         trade.discord_guild,
#     )

# trade_id = self.callback_payload["trade_id"]

# receiving_team_id = trade.team_lookup[self.values[0]]

# (
#     trade,
#     initiating_party,
#     initiating_party_role,
#     initiating_party_trade_channel,
#     receiving_party,
#     receiving_party_role,
#     receiving_party_trade_channel,
#     discord_guild,
# ) = await get_trade_info(trade_id, receiving_team_id)


def update_trade_view(handler: TaskHandler, trade: Trade, interaction=None):
    if trade.state == "new":
        everyone_role = interaction.guild.default_role
        initiating_party_discord_role: discord.Role = interaction.guild.get_role(
            trade.initiating_party.role.discord_id
        )

        if initiating_party_discord_role is None:
            async_to_sync(
                interaction.response.send_message(
                    content="Could not find initiating party role",
                    ephemeral=True,
                )
            )

            return

        receiving_party_discord_role: discord.Role = interaction.guild.get_role(
            trade.receiving_party.role.discord_id
        )

        if receiving_party_discord_role is None:
            async_to_sync(
                interaction.response.send_message(
                    content="Could not find receiving party role",
                    ephemeral=True,
                )
            )

            return

        overwrites = {
            everyone_role: discord.PermissionOverwrite(view_channel=False),
            initiating_party_discord_role: discord.PermissionOverwrite(
                view_channel=True
            ),
            receiving_party_discord_role: discord.PermissionOverwrite(
                view_channel=True
            ),
        }

        # Create the threads
        initiating_thread_name = f"Trade with {trade.receiving_party.name}"
        initiating_party_trade_thread = async_to_sync(handler.create_thread)(
            {
                "channel_id": trade.initiating_party.trade_channel.id,  # initiating party trade channel
                "message": f"{initiating_party_discord_role.mention}, your trade with {trade.receiving_party.name} has been created",  # ping that team
                "name": initiating_thread_name,  # trade with other team
            }
        )

        # create channel for trade
        trade.initiating_party_discord_thread, _ = Channel.objects.get_or_create(
            discord_id=initiating_party_trade_thread.id,
            guild=trade.discord_guild,
            name=initiating_party_trade_thread.name,
        )

        # Reply in old channel with link to the trade
        async_to_sync(interaction.response.send_message)(
            content=f"Trade channel created! You can access it here: {initiating_party_trade_thread.mention}",
            ephemeral=True,
        )

        from .Button import Button

        button_messsage = async_to_sync(handler.create_button)(
            {
                "guild_id": interaction.guild.id,
                "trade_id": trade.id,
                "channel_id": trade.initiating_party.trade_channel.discord_id,
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
                            "do_next": Button.currency_trade_adjustment_menu.__name__,
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
                            "do_next": Button.accept_trade.__name__,
                            "callback_payload": {"trade_id": trade.id},
                        },
                        {
                            "x": 2,
                            "y": 1,
                            "style": discord.ButtonStyle.primary,
                            "disabled": True,
                            "label": "Lock in trade",
                            "emoji": "🔒",
                            "do_next": Button.lock_in_trade.__name__,
                            "callback_payload": {"trade_id": trade.id},
                        },
                    ]
                ],
            },
        )

        # button_messsage = await handler.create_button(
        #     {
        #         "guild_id": interaction.guild.id,
        #         "trade_id": trade_id,
        #         "channel_id": receiving_party_trade_thread.id,
        #         "callback_payload": {},
        #         "button_rows": [
        #             [
        #                 {
        #                     "x": 0,
        #                     "y": 0,
        #                     "style": discord.ButtonStyle.primary,
        #                     "disabled": False,
        #                     "label": "Adjust trade amounts",
        #                     "custom_id": f"{trade.id}",
        #                     "emoji": "✏️",
        #                     "do_next": Button.currency_trade_adjustment_menu.__name__,
        #                     "callback_payload": {"trade_id": trade.id},
        #                 },
        #                 # {
        #                 #     "x": 0,
        #                 #     "y": 1,
        #                 #     "style": discord.ButtonStyle.danger,
        #                 #     "disabled": False,
        #                 #     "label": "Cancel trade",
        #                 #     "emoji": "❌",
        #                 #     "do_next": "cancel_trade",
        #                 #     "callback_payload": {"trade_id": trade.id},
        #                 # },
        #                 {
        #                     "x": 1,
        #                     "y": 1,
        #                     "style": discord.ButtonStyle.success,
        #                     "disabled": False,
        #                     "label": "Toggle Trade Accept",
        #                     "emoji": "✅",
        #                     "do_next": Button.accept_trade.__name__,
        #                     "callback_payload": {"trade_id": trade.id},
        #                 },
        #                 {
        #                     "x": 2,
        #                     "y": 1,
        #                     "style": discord.ButtonStyle.primary,
        #                     "disabled": True,
        #                     "label": "Lock in trade",
        #                     "emoji": "🔒",
        #                     "do_next": Button.lock_in_trade.__name__,
        #                     "callback_payload": {"trade_id": trade.id},
        #                 },
        #             ]
        #         ],
        #     },
        # )

        trade.embed_id = button_messsage.id

        trade.save()
