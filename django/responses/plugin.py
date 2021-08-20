import json
import logging

from asgiref.sync import sync_to_async

from bot.plugins.base import BasePlugin

# from discord import DMChannel
from .models import Response

logger = logging.getLogger(__name__)


class Plugin(BasePlugin):
    async def on_message(self, message):
        if message.reference:
            responses = await (
                sync_to_async(list)(
                    Response.objects.filter(question_id=message.reference.message_id)
                )
            )

            if len(responses) > 0:
                responses[0].response = message.content
                await sync_to_async(responses[0].save)()

                await message.add_reaction("👍")
