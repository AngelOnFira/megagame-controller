import logging

from asgiref.sync import sync_to_async
from bot.plugins.base import BasePlugin

from .services import CreateTransaction

logger = logging.getLogger(__name__)


class Plugin(BasePlugin):
    async def on_message(self, message):
        if message.content.startswith("!control send"):
            _, command, destination, amount, currency = tuple(
                message.content.split(" ")
            )

            print("Message", message.content)
            print("Currency", currency)

            await sync_to_async(CreateTransaction.execute)(
                {
                    "currency_name": currency,
                    "amount": amount,
                    "destination_wallet": destination,
                }
            )

            await message.author.send("Transaction Complete")
