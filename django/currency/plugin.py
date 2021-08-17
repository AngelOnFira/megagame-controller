import logging
import emojis
import dice
import discord

from asgiref.sync import sync_to_async
from bot.plugins.base import BasePlugin
from team.models import Team

from .services import CreateTransaction, UpdateTransaction
import json

logger = logging.getLogger(__name__)

class Dropdown(discord.ui.Select):
    def __init__(self):

        # Set the options that will be presented inside the dropdown
        options = [
            discord.SelectOption(label='Red', description='Your favourite colour is red', emoji='🟥'),
            discord.SelectOption(label='Green', description='Your favourite colour is green', emoji='🟦'),
            discord.SelectOption(label='Blue', description='Your favourite colour is blue', emoji='🟩')
        ]

        # The placeholder is what will be shown when no option is chosen
        # The min and max values indicate we can only pick one of the three options
        # The options parameter defines the dropdown options. We defined this above
        super().__init__(placeholder='Choose your favourite colour...', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        # Use the interaction object to send a response message containing
        # the user's favourite colour or choice. The self object refers to the
        # Select object, and the values attribute gets a list of the user's 
        # selected options. We only want the first one.
        await interaction.response.send_message(f'Your favourite colour is {self.values[0]}')

class DropdownView(discord.ui.View):
    def __init__(self):
        super().__init__()

        # Adds the dropdown to our view object.
        self.add_item(Dropdown())


class Plugin(BasePlugin):
    async def on_message(self, message):
        print(message)
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
            teams_sorted = await sync_to_async(list)(
                Team.objects.all().order_by("name")
            )

            team_text = "Starting transaction. Who would you like to trade with?\n\n"
            emoji_lookup = {}

            for team in teams_sorted:
                team_text += f"{team.name}: {emojis.encode(team.emoji)}\n"
                emoji_lookup[team.emoji] = team.name

            emoji_lookup_json = json.dumps(emoji_lookup)

            bank_message = await message.channel.send(team_text)
            for emoji in emoji_lookup.keys():
                await bank_message.add_reaction(emojis.encode(emoji))

            await sync_to_async(CreateTransaction.execute)(
                {
                    "message_id": bank_message.id,
                    "message_sender_id": bank_message.author.id,
                    "emoji_lookup": emoji_lookup,
                }
            )

        if message.content.startswith("!roll"):
            await message.reply(sum(dice.roll(message.content.split(" ")[1])))

        if message.content.startswith("!sys"):
            view = DropdownView()
            await message.channel.send("test", view=view)

    async def on_reaction_add(self, reaction, user):
        # TODO (foan): reactions aren't capturing after a server restart

        # If the reaction is from the bot, ignore it
        if user.bot:
            return

        (response, emoji_lookup) = await sync_to_async(UpdateTransaction.execute)(
            {
                "message_id": reaction.message.id,
                "reaction_emoji": emojis.decode(reaction.emoji),
            }
        )

        if response == emoji_lookup == None:
            return

        if response != None:
            await reaction.message.edit(content=response)

        await reaction.message.clear_reactions()

        if emoji_lookup != None:
            for emoji in emoji_lookup.keys():
                await reaction.message.add_reaction(emojis.encode(emoji))

        return await super().on_reaction_add(reaction, user)
