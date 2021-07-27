import logging
import emojis

from asgiref.sync import sync_to_async
from bot.plugins.base import BasePlugin

from .services import CreateTransaction, UpdateTransaction

logger = logging.getLogger(__name__)


class Plugin(BasePlugin):
    async def on_message(self, message):
        # await message.reply("test")
        if message.content.startswith("!control send"):
            _, command, destination, amount, currency = tuple(
                message.content.split(" ")
            )

            print("Message", message.content)
            print("Currency", currency)

            # await sync_to_async(CreateTransaction.execute)(
            #     {
            #         "currency_name": currency,
            #         "amount": amount,
            #         "destination_wallet": destination,
            #     }
            # )

            await message.author.send("Transaction Complete")

        if message.content.startswith("!bank"):

            # TODO (foan): check that there isn't a traction in progress

            bank_message = await message.channel.send(
                "Starting transaction\n:one: trade\n:two: purchase"
            )
            for emoji in ["1️⃣", "2️⃣"]:
                await bank_message.add_reaction(emoji)

            await sync_to_async(CreateTransaction.execute)(
                {
                    "message_id": bank_message.id,
                    "message_sender_id": bank_message.author.id,
                }
            )

    async def on_reaction_add(self, reaction, user):
        # await sync_to_async(UpdateTransaction.execute)(
        #         {
        #             "message_id": reaction.message.id,
        #             "reaction_emoji": emojis.decode(reaction.emoji)
        #         }
        #     )
        return await super().on_reaction_add(reaction, user)
