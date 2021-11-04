import logging

import discord
from asgiref.sync import async_to_sync, sync_to_async

from bot.discord_models.models import Channel
from bot.services.TaskHandler import TaskHandler
from currencies.models import Trade
from teams.models import Team

logger = logging.getLogger("bot")


def update_trade_view(handler: TaskHandler, trade: Trade, interaction=None):
    if trade.state in [
        "initiating_party_view",
        "receiving_party_view",
    ]:
        # Alternate the main team
        if trade.state == "initiating_party_view":
            party_name = trade.initiating_party.name
            other_party_name = trade.receiving_party.name
            party_trade_channel_id = trade.initiating_party.trade_channel.id
            party_role_id = trade.initiating_party.role.discord_id
            other_party_role_id = trade.receiving_party.role.discord_id

        elif trade.state == "receiving_party_view":
            party_name = trade.receiving_party.name
            other_party_name = trade.initiating_party.name
            party_trade_channel_id = trade.receiving_party.trade_channel.id
            party_role_id = trade.receiving_party.role.discord_id
            other_party_role_id = trade.initiating_party.role.discord_id

        trade.save()

        everyone_role = interaction.guild.default_role
        party_discord_role: discord.Role = interaction.guild.get_role(party_role_id)

        if party_discord_role is None:
            async_to_sync(
                interaction.response.send_message(
                    content="Could not find current party role",
                    ephemeral=True,
                )
            )

            return

        other_party_discord_role: discord.Role = interaction.guild.get_role(
            other_party_role_id
        )

        if other_party_discord_role is None:
            async_to_sync(
                interaction.response.send_message(
                    content="Could not find other party role",
                    ephemeral=True,
                )
            )

            return

        # overwrites = {
        #     everyone_role: discord.PermissionOverwrite(view_channel=False),
        #     initiating_party_discord_role: discord.PermissionOverwrite(
        #         view_channel=True
        #     ),
        #     receiving_party_discord_role: discord.PermissionOverwrite(
        #         view_channel=True
        #     ),
        # }

        # Create the threads
        thread_name = f"Trade with {party_name}"
        trade_thread = async_to_sync(handler.create_thread)(
            {
                "channel_id": party_trade_channel_id,  # initiating party trade channel
                "message": f"{party_discord_role.mention}, your trade with {other_party_name} has been created",  # ping that team
                "name": thread_name,  # trade with other team
            }
        )

        # create channel for trade
        trade.current_discord_trade_thread, _ = Channel.objects.get_or_create(
            discord_id=trade_thread.id,
            guild=trade.discord_guild,
            name=trade_thread.name,
        )

        trade.save()

        from .Button import Button

        button_messsage = async_to_sync(handler.create_button)(
            {
                "guild_id": interaction.guild.id,
                "trade_id": trade.id,
                "channel_id": trade.current_discord_trade_thread.discord_id,
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
        logger.debug(trade.current_discord_trade_thread)

        # print(trade.current_discord_trade_thread)

        trade.embed_id = button_messsage.id

        trade.save()
    else:
        logger.debug("Trade not in correct state")

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
