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
            "channel_discord_id": interaction.channel_id,
            "callback_payload": {},
            # "button_rows": [
            #     [
            #         {
            #             "x": 0,
            #             "y": 0,
            #             "style": discord.ButtonStyle.primary,
            #             "disabled": False,
            #             "label": "Buy 1",
            #             # "custom_id": f"{payment.id}-1",
            #             "emoji": "✅",
            #             "do_next": Button.confirm.__name__,
            #             "callback_payload": {
            #                 "success_callback": {
            #                     "do_next": Button.make_payment.__name__,
            #                     "callback_payload": {
            #                         "payment_id": payment.id,
            #                         "count": 1,
            #                     },
            #                 },
            #                 "fail_callback": {
            #                     "do_next": Button.cancel.__name__,
            #                     "callback_payload": {},
            #                 },
            #             },
            #         },
            #         {
            #             "x": 1,
            #             "y": 0,
            #             "style": discord.ButtonStyle.primary,
            #             "disabled": False,
            #             "label": "Buy 2",
            #             # "custom_id": f"{payment.id}-2",
            #             "emoji": "✅",
            #             "do_next": Button.confirm.__name__,
            #             "callback_payload": {
            #                 "success_callback": {
            #                     "do_next": Button.make_payment.__name__,
            #                     "callback_payload": {
            #                         "payment_id": payment.id,
            #                         "count": 2,
            #                     },
            #                 },
            #                 "fail_callback": {
            #                     "do_next": Button.cancel.__name__,
            #                     "callback_payload": {},
            #                 },
            #             },
            #         },
            #         {
            #             "x": 2,
            #             "y": 0,
            #             "style": discord.ButtonStyle.primary,
            #             "disabled": False,
            #             "label": "Buy 3",
            #             # "custom_id": f"{payment.id}-3",
            #             "emoji": "✅",
            #             "do_next": Button.confirm.__name__,
            #             "callback_payload": {
            #                 "success_callback": {
            #                     "do_next": Button.make_payment.__name__,
            #                     "callback_payload": {
            #                         "payment_id": payment.id,
            #                         "count": 3,
            #                     },
            #                 },
            #                 "fail_callback": {
            #                     "do_next": Button.cancel.__name__,
            #                     "callback_payload": {},
            #                 },
            #             },
            #         },
            #         {
            #             "x": 3,
            #             "y": 0,
            #             "style": discord.ButtonStyle.primary,
            #             "disabled": False,
            #             "label": "Buy 4",
            #             # "custom_id": f"{payment.id}-3",
            #             "emoji": "✅",
            #             "do_next": Button.confirm.__name__,
            #             "callback_payload": {
            #                 "success_callback": {
            #                     "do_next": Button.make_payment.__name__,
            #                     "callback_payload": {
            #                         "payment_id": payment.id,
            #                         "count": 4,
            #                     },
            #                 },
            #                 "fail_callback": {
            #                     "do_next": Button.cancel.__name__,
            #                     "callback_payload": {},
            #                 },
            #             },
            #         },
            #         {
            #             "x": 4,
            #             "y": 0,
            #             "style": discord.ButtonStyle.secondary,
            #             "disabled": False,
            #             "label": "Lock Payment (Control only)",
            #             # "custom_id": f"{payment.id}-lock-in",
            #             "do_next": Button.confirm.__name__,
            #             "callback_payload": {
            #                 "success_callback": {
            #                     "do_next": Button.lock_payment.__name__,
            #                     "callback_payload": {
            #                         "payment_id": payment.id,
            #                     },
            #                 },
            #                 "fail_callback": {
            #                     "do_next": Button.cancel.__name__,
            #                     "callback_payload": {},
            #                 },
            #             },
            #         },
            #     ]
            # ],
            "button_rows": [
                [
                    {
                        "x": 0,
                        "y": 0,
                        "style": discord.ButtonStyle.primary,
                        "disabled": False,
                        "label": "Buy 1",
                        "custom_id": f"{payment.id}",
                        "emoji": "✅",
                        "do_next": Button.make_payment.__name__,
                        "callback_payload": {"payment_id": payment.id, "count": 1},
                    },
                    {
                        "x": 1,
                        "y": 0,
                        "style": discord.ButtonStyle.primary,
                        "disabled": False,
                        "label": "Buy 2",
                        "custom_id": f"{payment.id}-2",
                        "emoji": "✅",
                        "do_next": Button.make_payment.__name__,
                        "callback_payload": {"payment_id": payment.id, "count": 2},
                    },
                    {
                        "x": 2,
                        "y": 0,
                        "style": discord.ButtonStyle.primary,
                        "disabled": False,
                        "label": "Buy 3",
                        "custom_id": f"{payment.id}-3",
                        "emoji": "✅",
                        "do_next": Button.make_payment.__name__,
                        "callback_payload": {"payment_id": payment.id, "count": 3},
                    },
                    {
                        "x": 3,
                        "y": 0,
                        "style": discord.ButtonStyle.primary,
                        "disabled": False,
                        "label": "Buy 4",
                        "custom_id": f"{payment.id}-4",
                        "emoji": "✅",
                        "do_next": Button.make_payment.__name__,
                        "callback_payload": {"payment_id": payment.id, "count": 4},
                    },
                    {
                        "x": 4,
                        "y": 0,
                        "style": discord.ButtonStyle.secondary,
                        "disabled": False,
                        "do_next": Button.lock_payment.__name__,
                        "label": (
                            "Lock Payment (Control only)"
                            if payment.fundraising_amount == 0
                            else "Cancel raising funds"
                        ),
                        "custom_id": f"{payment.id}-lock-in",
                        "callback_payload": {
                            "payment_id": payment.id,
                        },
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

    payment.refresh_from_db()

    message: discord.Message = async_to_sync(interaction.channel.fetch_message)(
        payment.embed_id
    )

    embed: discord.Embed = CreatePaymentEmbed.execute({"payment_id": payment.id})

    if payment.completed:
        async_to_sync(message.edit)(embed=embed, view=None)
    else:
        async_to_sync(message.edit)(embed=embed)
