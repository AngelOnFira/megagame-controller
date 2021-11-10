import logging

import discord
from asgiref.sync import async_to_sync, sync_to_async
from bot.discord_models.models import Channel
from bot.services.TaskHandler import TaskHandler
from currencies.models import Payment, Trade
from teams.models import Team

logger = logging.getLogger("bot")


def update_payment_view(
    handler: TaskHandler, payment: Payment, interaction: discord.Interaction
):
    # embed: discord.Embed = discord.Embed(
    #     title=f"Payment", description=f"{payment.action}\nCost: {payment.cost}"
    # )

    # discord_message = async_to_sync(interaction.response.send_message)(
    #     embed=embed, ephemeral=False
    # )

    from .Button import Button

    button_messsage = async_to_sync(handler.create_button)(
        {
            "guild_id": interaction.guild.id,
            "payment_id": payment.id,
            "channel_id": interaction.channel_id,
            "callback_payload": {},
            "button_rows": [
                [
                    {
                        "x": 0,
                        "y": 0,
                        "style": discord.ButtonStyle.primary,
                        "disabled": False,
                        "label": f"Pay {payment.cost}",
                        "custom_id": f"{payment.id}",
                        "emoji": "✅",
                        "do_next": Button.currency_trade_adjustment_menu.__name__,
                        "callback_payload": {"payment_id": payment.id},
                    },
                ]
            ],
        },
    )
