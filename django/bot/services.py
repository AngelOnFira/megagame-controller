import json

import discord
import emojis
from aiohttp import payload
from asgiref.sync import async_to_sync, sync_to_async
from currencies.services import CreateTrade, CreateTradeEmbed, SelectTradeReceiver
from django import forms
from service_objects.fields import DictField, ListField, ModelField
from service_objects.services import Service
from tasks.models import TaskType
from tasks.services import QueueTask
from teams.models import Team

from bot.users.models import Member


@sync_to_async
def build_trade_buttons(channel_id, guild_id, trade_id):
    from currencies.models import Currency
    from tasks.models import TaskType
    from tasks.services import QueueTask

    button_rows = []

    currency: Currency
    for i, currency in enumerate(Currency.objects.all()):
        row = []

        for j, label in enumerate(["-5", "-1", "+1", "+5"]):
            style = discord.ButtonStyle.danger if j < 2 else discord.ButtonStyle.success

            # TODO: Track which team this button is associated with

            value_button = {
                "x": j,
                "y": i,
                "style": style,
                "disabled": False,
                "label": label,
                "custom_id": f"{currency.id}|{trade_id}|{label}",
            }

            row.append(value_button)

        currency_button = {
            "x": 4,
            "y": i,
            "style": discord.ButtonStyle.primary,
            "emoji": emojis.encode(currency.emoji),
            "disabled": True,
            "label": currency.name,
        }
        row.append(currency_button)

        button_rows.append(row)

    QueueTask.execute(
        {
            "task_type": TaskType.CREATE_BUTTONS,
            "payload": {
                "channel_id": channel_id,
                "guild_id": guild_id,
                "button_rows": button_rows,
                "trade_id": trade_id,
            },
        }
    )


class Dropdown(discord.ui.Select):
    async def callback(self, interaction: discord.Interaction):
        await self.callback_function(self, interaction)

    def __init__(self, options, callback, do_next=""):
        super().__init__(**options)
        self.callback_function = callback
        self.do_next = do_next


class Button(discord.ui.Button):
    # async def callback(self, interaction: discord.Interaction):
    #     await self.callback_function(self, interaction)

    def __init__(
        self,
        x: int,
        y: int,
        options: dict,
        view: discord.ui.View,
        callback=False,
        do_next: str = "",
    ):
        super().__init__(**options)
        self.x = x
        self.y = y
        # self.callback_function = callback
        self.do_next = do_next
        self.view_base = view

    async def callback(self, interaction: discord.Interaction):
        from currencies.models import Currency, Trade, Transaction
        from currencies.services import CreateTrade, CreateTradeEmbed
        from tasks.models import TaskType
        from tasks.services import QueueTask
        from teams.models import Team

        from bot.users.models import Member

        assert self.view is not None

        content = "test"

        async def adjust_currency_trade(inteaction: discord.Interaction):

            # Get the id
            # Get a transaction model and add or remove from the currency

            currency_id, trade_id, adjustment = self.custom_id.split("|")

            currency = await sync_to_async(Currency.objects.get)(id=currency_id)

            # Have to wrap it since it needs a prefetch
            @sync_to_async
            def get_trade(trade_id):
                trade = Trade.objects.prefetch_related(
                    "initiating_party", "receiving_party"
                ).get(id=trade_id)

                from_wallet = trade.initiating_party.wallet
                to_wallet = trade.receiving_party.wallet

                return trade, from_wallet, to_wallet

            trade, from_wallet, to_wallet = await get_trade(trade_id)

            transaction, _ = await sync_to_async(Transaction.objects.get_or_create)(
                trade=trade,
                currency=currency,
                defaults={
                    "amount": 0,
                    # TODO: Once team for button is tracked, swap this out
                    "from_wallet": from_wallet,
                    "to_wallet": to_wallet,
                },
            )

            transaction.amount += int(adjustment)
            transaction.amount = max(transaction.amount, 0)

            if transaction.amount == 0:
                await sync_to_async(transaction.delete)()
            else:
                await sync_to_async(transaction.save)()

            # TODO: Make sure they have enough money

            embed = await sync_to_async(CreateTradeEmbed.execute)({"trade": trade})

            await interaction.response.edit_message(embed=embed, view=self.view)

        async def start_trading(inteaction: discord.Interaction):
            options = []
            team_lookup = {}

            @sync_to_async
            def get_sender_team(author_id):
                from bot.users.models import Member

                team = Member.objects.get(discord_id=author_id).player.team

                return team, team.general_channel, team.guild

            sender_team, sender_team_channel, sender_team_guild = await get_sender_team(
                interaction.message.author.id
            )

            teams = await sync_to_async(list)(Team.objects.all())

            for team in teams:
                if not team.emoji or team.id == sender_team.id:
                    continue

                options.append(
                    {
                        "label": team.name,
                        "description": "",
                        "emoji": emojis.encode(team.emoji),
                    }
                )

                team_lookup[team.name] = team.id

            trade = await sync_to_async(CreateTrade.execute)(
                {
                    "initiating_team": sender_team,
                    "team_lookup": team_lookup,
                }
            )

            trade.discord_channel = sender_team_channel
            trade.discord_guild = sender_team_guild

            await sync_to_async(trade.save)()

            handler = TaskHandler(view=self.view_base)

            handler.create_dropdown_response(
                interaction,
                {
                    "placeholder": "Which country do you want to trade with?",
                    "min_values": 1,
                    "max_values": 1,
                    "options": options,
                },
            )

            # await sync_to_async(QueueTask.execute)(
            #     {
            #         "task_type": TaskType.CREATE_DROPDOWN,
            #         "payload": {
            #             "channel_id": interaction.channel.id,
            #             "guild_id": interaction.guild.id,
            #             "do_next": "",
            #             "dropdown": {
            #                 "placeholder": "Which country do you want to trade with?",
            #                 "min_values": 1,
            #                 "max_values": 1,
            #                 "options": options,
            #             },
            #         },
            #     }
            # )

        function_lookup = {
            "adjust_currency_trade": adjust_currency_trade,
            "start_trading": start_trading,
        }

        await function_lookup[self.do_next](interaction)

class ButtonView(discord.ui.View):
    def __init__(self):
        super().__init__()

        # Adds the dropdown to our view object.
        self.add_item(Button())


class TaskHandler:
    def __init__(self, view=None, client=None):
        self.view = view
        self.client = client

    def create_dropdown_response(
        self, interaction: discord.Interaction, options: dict, callback=None
    ):
        self.view.add_item(
            Dropdown(
                {
                    "placeholder": "Which country do you want to trade with?",
                    "min_values": 1,
                    "max_values": 1,
                    "options": options,
                },
                callback,
            )
        )
        async_to_sync(interaction.response.send_message)(
            content="test", view=self.view, ephemeral=True
        )

    def create_dropdown(self, payload: dict):
        guild_id = payload["guild_id"]
        channel_id = payload["channel_id"]
        dropdown = payload["dropdown"]
        do_next = payload["do_next"]

        async def callback(self: Dropdown, interaction: discord.Interaction):
            if self.do_next["type"] == TaskType.TRADE_SELECT_RECEIVER:
                await sync_to_async(SelectTradeReceiver.execute)(
                    {
                        "payload": self.do_next["payload"],
                        "values": self.values,
                    }
                )

                await build_trade_buttons(
                    channel_id, guild_id, self.do_next["payload"]["trade_id"]
                )

        options = []

        for option in dropdown["options"]:
            options.append(discord.SelectOption(**option))

        self.view.add_item(
            Dropdown(
                {
                    "placeholder": "Which country do you want to trade with?",
                    "min_values": 1,
                    "max_values": 1,
                    "options": options,
                },
                callback,
                do_next=do_next,
            )
        )
        channel = self.client.get_guild(guild_id).get_channel(channel_id)

        embedVar = discord.Embed(title=" ads", description=" d", color=0x00FF00)

        async_to_sync(channel.send)(embed=embedVar, view=self.view)


discord.ui.View()
