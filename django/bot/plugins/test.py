import logging

from bot.plugins.base import BasePlugin

logger = logging.getLogger("bot")


class Plugin(BasePlugin):
    async def on_message(self, message):
        channel = getattr(message.channel, "name", None)
        if channel != "developer":
            return

        if message.content.startswith("!pm"):
            await message.author.send("HAI")
