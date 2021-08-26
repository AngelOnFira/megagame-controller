import json
from code import interact

import discord
import emojis
from aiohttp import payload
from asgiref.sync import async_to_sync, sync_to_async
from service_objects.fields import DictField, ListField, ModelField
from service_objects.services import Service

from bot.discord_models.models import Category, Channel, Guild
from bot.users.models import Member
from currencies.models import Trade
from currencies.services import CreateTrade, CreateTradeEmbed, SelectTradeReceiver
from django import forms
from tasks.models import TaskType
from tasks.services import QueueTask
from teams.models import Team


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
        async def trade_country_chosen(interaction: discord.Interaction):
            # create channel for trade
            # need interaction author team, interaction trade?
            pass

            # get the trade category

            trade_category = list(
                filter(
                    lambda x: x.name.lower() == "trades", interaction.guild.categories
                )
            )

            assert len(trade_category) == 1

            trade_id = self.callback_payload["trade_id"]

            trade: Trade = await sync_to_async(Trade.objects.get)(id=trade_id)

            receiving_team_id = trade.team_lookup[self.values[0]]

            trade.receiving_party = await sync_to_async(Team.objects.get)(
                id=trade.team_lookup[self.values[0]]
            )

            @sync_to_async
            def get_involved_teams(trade: Trade):
                assert trade.initiating_party is not None
                assert trade.receiving_party is not None
                return (
                    trade.initiating_party,
                    trade.receiving_party,
                    trade.discord_guild,
                )

            initiating_party, receiving_party, discord_guild = await get_involved_teams(
                trade
            )

            text_channel = await interaction.guild.create_text_channel(
                f"Trade for {initiating_party.name} and {receiving_party.name}",
                category=trade_category[0],
            )

            # # get guild
            # guild, _ = await sync_to_async(Guild.objects.get)(id=interaction.guild.id)

            # create channel for trade
            new_channel, _ = await sync_to_async(Channel.objects.get_or_create)(
                discord_id=text_channel.id, guild=discord_guild
            )

            trade.discord_channel = new_channel

            await sync_to_async(trade.save)()

            # Reply in old channel with link to the trade
            await interaction.response.send_message(
                content=f"Trade channel created! You can access it here: {text_channel.mention}",
                ephemeral=True,
            )

        function_lookup = {
            "trade_country_chosen": trade_country_chosen,
        }

        await function_lookup[self.do_next](interaction)

    def __init__(self, options, do_next, callback_payload: dict):
        super().__init__(**options)
        self.do_next = do_next
        self.callback_payload = callback_payload


class Button(discord.ui.Button):
    # async def callback(self, interaction: discord.Interaction):
    #     await self.callback_function(self, interaction)

    def __init__(
        self,
        x: int,
        y: int,
        options: dict,
        view: discord.ui.View,
        do_next: str = "",
    ):
        super().__init__(**options)
        self.x = x
        self.y = y
        self.do_next = do_next
        self.view_base = view

    async def callback(self, interaction: discord.Interaction):
        from bot.users.models import Member
        from currencies.models import Currency, Trade, Transaction
        from currencies.services import CreateTrade, CreateTradeEmbed
        from tasks.models import TaskType
        from tasks.services import QueueTask
        from teams.models import Team

        assert self.view is not None

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
            options: list[discord.SelectOption] = []
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
                    discord.SelectOption(
                        label=team.name,
                        description="",
                        emoji=emojis.encode(team.emoji),
                    )
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

            handler = TaskHandler(view=discord.ui.View())

            await handler.create_dropdown_response(
                interaction, options, "trade_country_chosen", {"trade_id": trade.id}
            )

        function_lookup = {
            "adjust_currency_trade": adjust_currency_trade,
            "start_trading": start_trading,
        }

        await function_lookup[self.do_next](interaction)


# class ButtonView(discord.ui.View):
#     def __init__(self):
#         super().__init__()

#         # Adds the dropdown to our view object.
#         self.add_item(Button())


class TaskHandler:
    def __init__(self, view=None, client=None):
        self.view = view
        self.client = client

    async def create_dropdown_response(
        self,
        interaction: discord.Interaction,
        options: list[discord.SelectOption],
        do_next: str,
        callback_payload: dict,
    ):
        self.view.add_item(
            Dropdown(
                {
                    "placeholder": "Which country do you want to trade with?",
                    "min_values": 1,
                    "max_values": 1,
                    "options": options,
                },
                do_next,
                callback_payload,
            )
        )

        await interaction.response.send_message(
            content="test", view=self.view, ephemeral=True
        )

    async def create_dropdown(self, payload: dict):
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

    async def create_category(self, payload: dict):
        guild_id = payload["guild_id"]
        print(guild_id)

        guild: discord.Guild = self.client.get_guild(guild_id)
        if guild is None:
            raise Exception("Guild not found")

        everyone_role = guild.default_role

        overwrites = {
            everyone_role: discord.PermissionOverwrite(view_channel=True),
        }

        # Category can either be created for a team or everyone
        if "team_id" in payload:
            team_id = payload["team_id"]

            @sync_to_async
            def get_team(team_id):
                team = Team.objects.get(id=team_id)
                team_guild = team.guild
                team_role = team.role

                return team, team_guild, team_role

            team, team_guild, team_role = await get_team(team_id)

            team_role_id = team_role.discord_id
            team_role = guild.get_role(team_role_id)

            overwrites[everyone_role] = discord.PermissionOverwrite(view_channel=False)

            overwrites[team_role] = discord.PermissionOverwrite(view_channel=True)

            category_name = team.name

        else:
            category_name = payload["category_name"]

        category_channel = await guild.create_category(
            category_name,
            overwrites=overwrites,
        )

        if "team_id" in payload:
            team.category, _ = await sync_to_async(Category.objects.get_or_create)(
                discord_id=category_channel.id, guild=team_guild
            )

            await sync_to_async(team.save)()


discord.ui.View()
