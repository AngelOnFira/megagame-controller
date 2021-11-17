import logging

import discord
from asgiref.sync import async_to_sync, sync_to_async
from bot.discord_models.models import Channel
from bot.services.TaskHandler import TaskHandler
from currencies.models import Payment, Trade
from currencies.services import CreatePaymentEmbed
from teams.models import Team

logger = logging.getLogger("bot")


def create_payment_view(
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
                        "label": f"Buy 1 (Pay {payment.cost})",
                        "custom_id": f"{payment.id}",
                        "emoji": "✅",
                        "do_next": Button.make_payment.__name__,
                        "callback_payload": {"payment_id": payment.id, "multiplier": 1},
                    },
                    {
                        "x": 1,
                        "y": 0,
                        "style": discord.ButtonStyle.primary,
                        "disabled": False,
                        "label": f"Buy 2 (Pay {payment.cost*2})",
                        "custom_id": f"{payment.id}-2",
                        "emoji": "✅",
                        "do_next": Button.make_payment.__name__,
                        "callback_payload": {"payment_id": payment.id, "multiplier": 2},
                    },
                    {
                        "x": 2,
                        "y": 0,
                        "style": discord.ButtonStyle.primary,
                        "disabled": False,
                        "label": f"Buy 3 (Pay {payment.cost*3})",
                        "custom_id": f"{payment.id}-3",
                        "emoji": "✅",
                        "do_next": Button.make_payment.__name__,
                        "callback_payload": {"payment_id": payment.id, "multiplier": 3},
                    },
                ]
            ],
        },
    )

    payment.embed_id = button_messsage.id

    payment.save()

    async_to_sync(interaction.response.send_message)(
        content="Payment created", ephemeral=True
    )


def update_payment_view(payment: Payment, interaction: discord.Interaction):

    from .Button import Button

    message: discord.Message = async_to_sync(interaction.channel.fetch_message)(
        payment.embed_id
    )

    embed: discord.Embed = CreatePaymentEmbed.execute({"payment_id": payment.id})

    async_to_sync(message.edit)(embed=embed)
