import json
from code import interact
from typing import Tuple

import discord
import emojis
from asgiref.sync import sync_to_async

from bot.discord_models.models import Category, Channel, Guild, Role
from bot.users.models import Member
from currencies.models import Currency, Trade
from currencies.services import CreateBankEmbed, CreateTradeEmbed
from players.models import Player
from responses.models import Response
from teams.models import Team

TEAM_ROLE_COLOUR = discord.Colour.red()


class Dropdown(discord.ui.Select):
    def __init__(self, client, options, do_next, callback_payload: dict):
        super().__init__(**options)

        assert client is not None
        self.client: discord.Client = client

        self.do_next = do_next
        self.callback_payload = callback_payload

    async def callback(self, interaction: discord.Interaction):
        async def trade_country_chosen(interaction: discord.Interaction):
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
                id=receiving_team_id
            )

            await sync_to_async(trade.save)()

            @sync_to_async
            def get_involved_teams(
                trade: Trade,
            ) -> Tuple[Team, Role, Channel, Team, Role, Channel, Guild]:
                assert trade.initiating_party is not None
                assert trade.receiving_party is not None
                return (
                    trade.initiating_party,
                    trade.initiating_party.role,
                    trade.initiating_party.trade_channel,
                    trade.receiving_party,
                    trade.receiving_party.role,
                    trade.receiving_party.trade_channel,
                    trade.discord_guild,
                )

            (
                initiating_party,
                initiating_party_role,
                initiating_party_trade_channel,
                receiving_party,
                receiving_party_role,
                receiving_party_trade_channel,
                discord_guild,
            ) = await get_involved_teams(trade)

            everyone_role = interaction.guild.default_role
            initiating_party_role = interaction.guild.get_role(
                initiating_party_role.discord_id
            )

            if initiating_party_role is None:
                await interaction.response.send_message(
                    content="Could not find initiating party role",
                    ephemeral=True,
                )

                return

            receiving_party_role = interaction.guild.get_role(
                receiving_party_role.discord_id
            )

            if receiving_party_role is None:
                await interaction.response.send_message(
                    content="Could not find receiving party role",
                    ephemeral=True,
                )

                return

            overwrites = {
                everyone_role: discord.PermissionOverwrite(view_channel=False),
                initiating_party_role: discord.PermissionOverwrite(view_channel=True),
                receiving_party_role: discord.PermissionOverwrite(view_channel=True),
            }

            # Create handler to call creation methods directly
            handler = TaskHandler(
                view=discord.ui.View(timeout=None), client=self.client
            )

            # Create the threads
            initiating_thread_name = f"Trade with {receiving_party.name}"
            initiating_party_trade_thread = await handler.create_thread(
                {
                    "channel_id": initiating_party_trade_channel.id,  # initiating party trade channel
                    "message": f"{initiating_party_role.mention}, your trade with {receiving_party.name} has been created",  # ping that team
                    "name": initiating_thread_name,  # trade with other team
                }
            )

            # create channel for trade
            trade.initiating_party_discord_thread, _ = await sync_to_async(
                Channel.objects.get_or_create
            )(
                discord_id=initiating_party_trade_thread.id,
                guild=discord_guild,
                name=initiating_party_trade_thread.name,
            )

            receiving_thread_name = f"Trade with {initiating_party.name}"
            receiving_party_trade_thread = await handler.create_thread(
                {
                    "channel_id": receiving_party_trade_channel.id,
                    "message": f"{receiving_party_role.mention} a trade for you has been created by {initiating_party.name}",
                    "name": receiving_thread_name,
                }
            )

            trade.receiving_party_discord_thread, _ = await sync_to_async(
                Channel.objects.get_or_create
            )(
                discord_id=receiving_party_trade_thread.id,
                guild=discord_guild,
                name=receiving_party_trade_thread.name,
            )

            # Reply in old channel with link to the trade
            await interaction.response.send_message(
                content=f"Trade channel created! You can access it here: {initiating_party_trade_thread.mention}",
                ephemeral=True,
            )

            button_messsage = await handler.create_button(
                {
                    "guild_id": interaction.guild.id,
                    "trade_id": trade_id,
                    "channel_id": initiating_party_trade_thread.id,
                    "callback_payload": {},
                    "button_rows": [
                        [
                            {
                                "x": 0,
                                "y": 0,
                                "style": discord.ButtonStyle.primary,
                                "disabled": False,
                                "label": "Adjust trade amounts",
                                "custom_id": f"{trade.id}",
                                "emoji": "✏️",
                                "do_next": "currency_trade_currency_menu",
                                "callback_payload": {"trade_id": trade.id},
                            },
                            # {
                            #     "x": 0,
                            #     "y": 1,
                            #     "style": discord.ButtonStyle.danger,
                            #     "disabled": False,
                            #     "label": "Cancel trade",
                            #     "emoji": "❌",
                            #     "do_next": "cancel_trade",
                            #     "callback_payload": {"trade_id": trade.id},
                            # },
                            {
                                "x": 1,
                                "y": 1,
                                "style": discord.ButtonStyle.success,
                                "disabled": False,
                                "label": "Toggle Trade Accept",
                                "emoji": "✅",
                                "do_next": "accept_trade",
                                "callback_payload": {"trade_id": trade.id},
                            },
                            {
                                "x": 2,
                                "y": 1,
                                "style": discord.ButtonStyle.primary,
                                "disabled": True,
                                "label": "Lock in trade",
                                "emoji": "🔒",
                                "do_next": "lock_in_trade",
                                "callback_payload": {"trade_id": trade.id},
                            },
                        ]
                    ],
                },
            )

            button_messsage = await handler.create_button(
                {
                    "guild_id": interaction.guild.id,
                    "trade_id": trade_id,
                    "channel_id": receiving_party_trade_thread.id,
                    "callback_payload": {},
                    "button_rows": [
                        [
                            {
                                "x": 0,
                                "y": 0,
                                "style": discord.ButtonStyle.primary,
                                "disabled": False,
                                "label": "Adjust trade amounts",
                                "custom_id": f"{trade.id}",
                                "emoji": "✏️",
                                "do_next": "currency_trade_currency_menu",
                                "callback_payload": {"trade_id": trade.id},
                            },
                            # {
                            #     "x": 0,
                            #     "y": 1,
                            #     "style": discord.ButtonStyle.danger,
                            #     "disabled": False,
                            #     "label": "Cancel trade",
                            #     "emoji": "❌",
                            #     "do_next": "cancel_trade",
                            #     "callback_payload": {"trade_id": trade.id},
                            # },
                            {
                                "x": 1,
                                "y": 1,
                                "style": discord.ButtonStyle.success,
                                "disabled": False,
                                "label": "Toggle Trade Accept",
                                "emoji": "✅",
                                "do_next": "accept_trade",
                                "callback_payload": {"trade_id": trade.id},
                            },
                            {
                                "x": 2,
                                "y": 1,
                                "style": discord.ButtonStyle.primary,
                                "disabled": True,
                                "label": "Lock in trade",
                                "emoji": "🔒",
                                "do_next": "lock_in_trade",
                                "callback_payload": {"trade_id": trade.id},
                            },
                        ]
                    ],
                },
            )

            trade.embed_id = button_messsage.id

            await sync_to_async(trade.save)()

        async def adjustment_select_trade_currency(interaction: discord.Interaction):
            # get currency by name
            # replace this embed with buttons
            currency_name = self.values[0]

            currency: Currency = await sync_to_async(Currency.objects.get)(
                name=currency_name
            )

            view = discord.ui.View(timeout=None)

            for j, label in enumerate(["-5", "-1", "+1", "+5"]):
                style = (
                    discord.ButtonStyle.danger if j < 2 else discord.ButtonStyle.success
                )

                button = Button(
                    self.client,
                    j,
                    0,
                    {
                        "style": style,
                        "label": label,
                        "row": 1,
                    },
                    do_next="adjust_currency_trade",
                    callback_payload={
                        "trade_id": self.callback_payload["trade_id"],
                        "currency_id": currency.id,
                        "amount": int(label),
                    },
                )

                view.add_item(button)

            currency_button = Button(
                self.client,
                4,
                0,
                {
                    "style": discord.ButtonStyle.primary,
                    "label": currency.name,
                    "row": 1,
                    "emoji": emojis.encode(currency.emoji),
                    "disabled": True,
                },
                do_next="unreachable",
                callback_payload={},
            )

            view.add_item(currency_button)

            await interaction.response.send_message(
                view=view,
                content=f"Adjust how many {currency.name} you will send.",
                ephemeral=True,
            )

        function_lookup = {
            "trade_country_chosen": trade_country_chosen,
            "adjustment_select_trade_currency": adjustment_select_trade_currency,
        }

        await function_lookup[self.do_next](interaction)


async def trade_view(client, trade):
    view = discord.ui.View(timeout=None)

    view.add_item(
        Button(
            client,
            0,
            0,
            {
                "style": discord.ButtonStyle.primary,
                "label": "Adjust trade amounts",
                "row": 0,
                "emoji": "✏️",
            },
            do_next="currency_trade_currency_menu",
            callback_payload={"trade_id": trade.id},
        )
    )

    # view.add_item(
    #     Button(
    #         client,
    #         0,
    #         1,
    #         {
    #             "style": discord.ButtonStyle.danger,
    #             "label": "Cancel trade",
    #             "row": 1,
    #             "emoji": "❌",
    #         },
    #         do_next="cancel_trade",
    #         callback_payload={"trade_id": trade.id},
    #     )
    # )

    view.add_item(
        Button(
            client,
            0,
            1,
            {
                "style": discord.ButtonStyle.success,
                "label": "Toggle Trade Accept",
                "row": 1,
                "emoji": "✅",
            },
            do_next="accept_trade",
            callback_payload={"trade_id": trade.id},
        )
    )

    show_lock_in = not (
        trade.initiating_party_accepted and trade.receiving_party_accepted
    )

    view.add_item(
        Button(
            client,
            0,
            1,
            {
                "style": discord.ButtonStyle.primary,
                "label": "Lock in trade",
                "row": 1,
                "emoji": "🔒",
                "disabled": show_lock_in,
            },
            do_next="lock_in_trade",
            callback_payload={"trade_id": trade.id},
        )
    )

    return view


class Button(discord.ui.Button):
    def __init__(
        self,
        client,
        x: int,
        y: int,
        options: dict,
        do_next: str,
        callback_payload: dict,
    ):
        super().__init__(**options)
        self.client = client
        self.x = x
        self.y = y
        self.do_next = do_next
        self.callback_payload = callback_payload

    async def callback(self, interaction: discord.Interaction):
        from currencies.models import Currency, Trade, Transaction
        from currencies.services import CreateTrade, CreateTradeEmbed
        from teams.models import Team

        async def adjust_currency_trade(interaction: discord.Interaction):
            currency_id = self.callback_payload["currency_id"]
            trade_id = self.callback_payload["trade_id"]
            amount = self.callback_payload["amount"]

            @sync_to_async
            def get_trade(trade_id, currency_id):
                trade = Trade.objects.get(id=trade_id)
                currency = Currency.objects.get(id=currency_id)

                initiating_party_wallet = trade.initiating_party.wallet
                receiving_party_wallet = trade.receiving_party.wallet

                return trade, currency, initiating_party_wallet, receiving_party_wallet

            (
                trade,
                currency,
                initiating_party_wallet,
                receiving_party_wallet,
            ) = await get_trade(trade_id, currency_id)

            currency = await sync_to_async(Currency.objects.get)(id=currency_id)

            @sync_to_async
            def get_player_team_interacting(interaction):
                interacting_team = Member.objects.get(
                    discord_id=interaction.user.id
                ).player.team
                interacting_team_wallet = interacting_team.wallet
                return interacting_team, interacting_team_wallet

            (
                interacting_team,
                interacting_team_wallet,
            ) = await get_player_team_interacting(interaction)

            if interacting_team_wallet.id not in (
                initiating_party_wallet.id,
                receiving_party_wallet.id,
            ):
                await interaction.response.send_message(
                    content="You can't interact with this transaction as you're not on one of the teams!",
                    ephemeral=True,
                )
                return

            from_wallet = interacting_team_wallet
            to_wallet = (
                initiating_party_wallet
                if initiating_party_wallet.id != from_wallet.id
                else receiving_party_wallet
            )

            transaction, _ = await sync_to_async(Transaction.objects.get_or_create)(
                trade=trade,
                currency=currency,
                from_wallet=from_wallet,
                to_wallet=to_wallet,
                defaults={
                    "amount": 0,
                },
            )

            transaction.amount += amount
            transaction.amount = max(transaction.amount, 0)

            if transaction.amount == 0:
                await sync_to_async(transaction.delete)()
            else:
                await sync_to_async(transaction.save)()

            trade.initiating_party_accepted = False
            trade.receiving_party_accepted = False

            await sync_to_async(trade.save)()

            embed = await sync_to_async(CreateTradeEmbed.execute)(
                {"trade_id": trade_id}
            )

            message: discord.Message = await interaction.channel.fetch_message(
                trade.embed_id
            )

            view = await trade_view(self.client, trade)

            await message.edit(embed=embed, view=view)

        async def currency_trade_adjustment_menu(interaction: discord.Interaction):
            # payload: expect a currency id
            currencies: Currency = await sync_to_async(list)(Currency.objects.all())

            button_rows = []

            currency: Currency
            for i, currency in enumerate(currencies):
                row = []

                for j, label in enumerate(["-5", "-1", "+1", "+5"]):
                    style = (
                        discord.ButtonStyle.danger
                        if j < 2
                        else discord.ButtonStyle.success
                    )

                    value_button = {
                        "x": j,
                        "y": i,
                        "style": style,
                        "disabled": False,
                        "label": label,
                        "custom_id": f"{currency.id}|{self.callback_payload['trade_id']}|{label}",
                        "do_next": "adjust_currency_trade",
                        "callback_payload": {},
                    }

                    row.append(value_button)

                currency_button = {
                    "x": 4,
                    "style": discord.ButtonStyle.primary,
                    "emoji": emojis.encode(currency.emoji),
                    "disabled": True,
                    "label": currency.name,
                    "do_next": "unreachable",
                    "callback_payload": {},
                }
                row.append(currency_button)

                button_rows.append(row)

            handler = TaskHandler(discord.ui.View(timeout=None), self.client)

            await handler.create_button(
                {
                    "guild_id": interaction.guild.id,
                    "button_rows": button_rows,
                    "content": "Adjust this trade",
                },
                interaction=interaction,
            )

        async def currency_trade_currency_menu(interaction: discord.Interaction):
            currencies: Currency = await sync_to_async(list)(Currency.objects.all())

            options = []

            for currency in currencies:
                options.append(
                    discord.SelectOption(
                        label=currency.name,
                        emoji=emojis.encode(currency.emoji),
                    )
                )

            handler = TaskHandler(discord.ui.View(timeout=None), self.client)

            dropdown_message = await handler.create_dropdown_response(
                interaction,
                options,
                "adjustment_select_trade_currency",
                {"trade_id": self.callback_payload["trade_id"]},
            )

        # From the team menu, "Start Trading" was pushed
        async def start_trading(interaction: discord.Interaction):
            options: list[discord.SelectOption] = []
            team_lookup = {}

            @sync_to_async
            def get_sender_team(interaction):
                from bot.users.models import Member

                channel_team = Channel.objects.get(
                    discord_id=interaction.channel.id
                ).team_menu_channel

                interacting_team = Member.objects.get(
                    discord_id=interaction.user.id
                ).player.team

                teams = list(Team.objects.all())

                return (
                    channel_team,
                    interacting_team,
                    interacting_team.guild,
                    teams,
                )

            (
                channel_team,
                interacting_team,
                interacting_team_guild,
                teams,
            ) = await get_sender_team(interaction)

            if channel_team.id != interacting_team.id:
                interacting_team = channel_team

                # TODO: Add check back
                # await interaction.response.send_message(
                #     content="You are not on this team!", ephemeral=True
                # )
                # return

            for team in teams:
                print(team)
                if not team.emoji or team.id == interacting_team.id:
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
                    "initiating_team": interacting_team,
                    "team_lookup": team_lookup,
                }
            )

            trade.discord_guild = interacting_team_guild

            handler = TaskHandler(discord.ui.View(timeout=None), self.client)

            dropdown_message = await handler.create_dropdown_response(
                interaction, options, "trade_country_chosen", {"trade_id": trade.id}
            )

            await sync_to_async(trade.save)()

        # When toggle trade accept is pressed
        async def accept_trade(interaction: discord.Interaction):
            trade_id = self.callback_payload["trade_id"]

            @sync_to_async
            def get_trade(trade_id, interaction):
                trade: Trade = Trade.objects.get(id=trade_id)
                interacting_team: Member = Member.objects.get(
                    discord_id=interaction.user.id
                ).player.team

                return (
                    trade,
                    interacting_team,
                    trade.initiating_party,
                    trade.receiving_party,
                )

            (
                trade,
                interacting_team,
                trade_initiating_party,
                trade_receiving_party,
            ) = await get_trade(trade_id, interaction)

            if interacting_team.id == trade_initiating_party.id:
                trade.initiating_party_accepted = not trade.initiating_party_accepted
            elif interacting_team.id == trade_receiving_party.id:
                trade.receiving_party_accepted = not trade.receiving_party_accepted

            await sync_to_async(trade.save)()

            embed = await sync_to_async(CreateTradeEmbed.execute)(
                {"trade_id": trade_id}
            )

            message: discord.Message = await interaction.channel.fetch_message(
                trade.embed_id
            )

            view = await trade_view(self.client, trade)

            await message.edit(embed=embed, view=view)

        async def lock_in_trade(interaction: discord.Interaction):
            # get the trade id
            # TODO: Make sure there is enough money
            trade_id = self.callback_payload["trade_id"]

            # Make the database queries
            @sync_to_async
            def get_trade(trade_id):
                trade = Trade.objects.get(id=trade_id)

                return (
                    trade,
                    list(trade.transactions.all()),
                    trade.initiating_party.menu_channel.discord_id,
                    trade.initiating_party.bank_embed_id,
                    trade.initiating_party.id,
                    trade.receiving_party.menu_channel.discord_id,
                    trade.receiving_party.bank_embed_id,
                    trade.receiving_party.id,
                )

            (
                trade,
                transactions,
                menu_channel_initiating_id,
                bank_initiating_embed_id,
                initiating_team_id,
                menu_channel_receiving_id,
                bank_receiving_embed_id,
                receiving_team_id,
            ) = await get_trade(trade_id)

            # Set the state of the trade
            completed = await sync_to_async(trade.complete)()

            if completed == False:
                await interaction.response.send_message(
                    content="One of the teams did not have enough of at least one currency to complete the transaction."
                )

                await sync_to_async(trade.reset)()

                trade.initiating_party_accepted = False
                trade.receiving_party_accepted = False

                await sync_to_async(trade.save)()

                return

            await sync_to_async(trade.save)()

            # Go through each attached transaction, and make sure it's set to complete
            for transaction in transactions:
                await sync_to_async(transaction.complete)()
                await sync_to_async(transaction.save)()

            # Change the embed on the menu channel for the initiating party
            menu_channel_initiating = interaction.guild.get_channel(
                menu_channel_initiating_id
            )
            initiating_message: discord.Message = await (
                menu_channel_initiating.fetch_message(bank_initiating_embed_id)
            )
            initiating_embed = await sync_to_async(CreateBankEmbed.execute)(
                {"team_id": initiating_team_id}
            )
            await initiating_message.edit(embed=initiating_embed)

            # Change the embed on the menu channel for the receiving party
            menu_channel_receiving = interaction.guild.get_channel(
                menu_channel_receiving_id
            )
            receiving_message: discord.Message = await (
                menu_channel_receiving.fetch_message(bank_receiving_embed_id)
            )
            receiving_embed = await sync_to_async(CreateBankEmbed.execute)(
                {"team_id": receiving_team_id}
            )
            await receiving_message.edit(embed=receiving_embed)

            await interaction.response.send_message(
                content="This trade is complete, and this channel will lock itself"
            )

            # TODO: Lock down channel

        function_lookup = {
            "accept_trade": accept_trade,
            "adjust_currency_trade": adjust_currency_trade,
            "currency_trade_adjustment_menu": currency_trade_adjustment_menu,
            "currency_trade_currency_menu": currency_trade_currency_menu,
            "lock_in_trade": lock_in_trade,
            "start_trading": start_trading,
        }

        await function_lookup[self.do_next](interaction)


class TaskHandler:
    def __init__(self, view: discord.ui.View, client: discord.Client):
        self.view = view

        assert client is not None
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
                self.client,
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
            content="_🔽_", view=self.view, ephemeral=True
        )

    # async def create_dropdown(self, payload: dict):
    #     guild_id = payload["guild_id"]
    #     channel_id = payload["channel_id"]
    #     dropdown = payload["dropdown"]
    #     do_next = payload["do_next"]

    #     options = []

    #     for option in dropdown["options"]:
    #         options.append(discord.SelectOption(**option))

    #     self.view.add_item(
    #         Dropdown(
    #             self.client,
    #             {
    #                 "placeholder": "Which country do you want to trade with?",
    #                 "min_values": 1,
    #                 "max_values": 1,
    #                 "options": options,
    #             },
    #             callback,
    #             do_next=do_next,
    #         )
    #     )
    #     channel = self.client.get_guild(guild_id).get_channel(channel_id)

    #     embedVar = discord.Embed(title=" ads", description=" d", color=0x00FF00)

    #     async_to_sync(channel.send)(embed=embedVar, view=self.view)

    async def create_category(self, payload: dict):
        guild_id = payload["guild_id"]

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
            def get_team(team_id) -> Tuple[Team, Guild, Role]:
                team = Team.objects.get(id=team_id)
                team_guild = team.guild
                team_role = team.role

                return (team, team_guild, team_role)

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

    async def create_button(
        self, payload: dict, interaction: discord.Interaction = None
    ):
        button_rows = payload["button_rows"]

        view = discord.ui.View(timeout=None)

        for row in button_rows:
            for button in row:
                options_dict = {
                    "style": button["style"][1],
                    "label": button["label"],
                    "row": button["y"],
                }

                if "emoji" in button:
                    options_dict["emoji"] = button["emoji"]

                if "disabled" in button:
                    options_dict["disabled"] = button["disabled"]

                if "custom_id" in button:
                    options_dict["custom_id"] = button["custom_id"]

                assert button["do_next"] != ""

                button = Button(
                    self.client,
                    button["x"],
                    button["y"],
                    options_dict,
                    do_next=button["do_next"],
                    callback_payload=button["callback_payload"],
                )

                view.add_item(button)

        params = {}

        if "trade_id" in payload:
            trade_id = payload["trade_id"]
            params["embed"] = await sync_to_async(CreateTradeEmbed.execute)(
                {"trade_id": trade_id}
            )
        elif "embed" in payload:
            params["embed"] = discord.Embed(**payload["embed"])
        elif "content" in payload:
            params["content"] = payload["content"]

        if interaction is None:
            guild_id = payload["guild_id"]
            if "channel_id" in payload:
                channel_id = payload["channel_id"]
            elif "team_id" in payload:
                team_id = payload["team_id"]

                @sync_to_async
                def get_channel_id(team_id):
                    return Team.objects.get(id=team_id).menu_channel.discord_id

                channel_id = await get_channel_id(team_id)
            else:
                raise Exception("No channel or team id found; don't know how to handle")

            channel = self.client.get_guild(guild_id).get_channel_or_thread(channel_id)
            print("Channel", channel)
            print("Threads", await self.client.get_guild(guild_id).active_threads())

            button_message = await channel.send(**params, view=view)
            return button_message

        else:
            await interaction.response.send_message(**params, view=view, ephemeral=True)

    async def create_channel(self, payload: dict):
        team_id = payload["team_id"]
        channel_bind_model_id = payload["channel_bind_model_id"]

        @sync_to_async
        def get_team(team_id):
            team = Team.objects.get(id=team_id)

            channel = Channel.objects.get(id=channel_bind_model_id)

            return team.category, team.guild, channel

        team_category, team_guild, channel = await get_team(team_id)

        guild = self.client.get_guild(team_guild.discord_id)

        # TODO: Remove fetch needed for cache busting
        category = await guild.fetch_channel(team_category.discord_id)

        text_channel = await guild.create_text_channel(
            channel.name,
            category=category,
        )

        channel.discord_id = text_channel.id

        await sync_to_async(channel.save)()

    async def create_role(self, payload: dict):
        team_id = payload["team_id"]

        @sync_to_async
        def get_team(team_id):
            team = Team.objects.get(id=team_id)
            team_guild = team.guild

            return team, team_guild

        team, team_guild = await get_team(team_id)

        # TODO: Problem with resetting db and running this

        roles = self.client.get_guild(team_guild.discord_id).roles
        role_dict = {}
        for role in roles:
            role_dict[role.name] = role

        role_names = [role.name for role in roles]

        # Check if the team is already in the guild
        if team.name in role_names:
            await role_dict[team.name].delete()

        # Create a role for the team
        role_object = await self.client.get_guild(team_guild.discord_id).create_role(
            name=team.name, hoist=True, mentionable=True, colour=TEAM_ROLE_COLOUR
        )

        new_role, _ = await sync_to_async(Role.objects.get_or_create)(
            discord_id=role_object.id, name=team.name, guild=team_guild
        )

        team.role = new_role
        await sync_to_async(team.save)()

    async def send_message(self, payload: dict):
        player_id = payload["player_id"]
        message = payload["message"]

        player = await sync_to_async(Player.objects.get)(id=player_id)

        discord_user: discord.User = await self.client.fetch_user(
            player.discord_member.discord_id
        )
        discord_message: discord.Message = await discord_user.send(message)

        @sync_to_async
        def update_player(discord_message):
            response = Response.objects.create(question_id=discord_message.id)
            player.responses.add(response)
            player.save()

        await update_player(discord_message)

    async def change_team(self, payload: dict):
        player_id = payload["player_id"]
        new_team_id = payload["new_team_id"]

        @sync_to_async
        def get_models(player_id, new_team_id):
            player = Player.objects.get(id=player_id)
            new_team = Team.objects.get(id=new_team_id)
            teams = [team for team in Team.objects.all()]

            player_guild = player.guild
            discord_member = player.discord_member
            team_role = new_team.role

            return (
                player,
                new_team,
                teams,
                player_guild,
                discord_member,
                team_role,
            )

        (
            player,
            new_team,
            teams,
            player_guild,
            discord_member,
            team_role,
        ) = await get_models(player_id, new_team_id)

        guild: Guild = self.client.get_guild(player_guild.discord_id)

        # TODO: Try to change this to get_member
        discord_member = await guild.fetch_member(discord_member.discord_id)

        # Will remove all roles from the player
        await discord_member.remove_roles(
            *[guild.get_role(team_role.discord_id) for team in teams]
        )

        # Add the new team role
        await discord_member.add_roles(guild.get_role(team_role.discord_id))

        player.team = new_team
        await sync_to_async(player.save)()

    async def create_message(self, payload: dict):
        channel_id = payload["channel_id"]
        message = payload["message"]

        channel = await sync_to_async(Channel.objects.get)(id=channel_id)
        discord_channel = self.client.get_channel(channel.discord_id)

        send_params = {}
        if message == "team_bank_embed":
            embed = send_params["embed"] = await sync_to_async(CreateBankEmbed.execute)(
                {
                    "team_id": payload["team_id"],
                }
            )

            discord_message = await discord_channel.send(embed=embed)

            team = await sync_to_async(Team.objects.get)(id=payload["team_id"])

            team.bank_embed_id = discord_message.id
            await sync_to_async(team.save)()

        # if message == "team_bank_embed":
        #     await sync_to_async(messag)()

    async def create_thread(self, payload: dict):
        from discord.enums import ChannelType

        channel_id = payload["channel_id"]
        message = payload["message"]
        name = payload["name"]

        channel: Channel = await sync_to_async(Channel.objects.get)(id=channel_id)
        discord_channel: discord.TextChannel = self.client.get_channel(
            channel.discord_id
        )

        new_thread = await discord_channel.create_thread(
            name=name,
            type=ChannelType.public_thread,
            # message=discord_message,
            auto_archive_duration=1440,
        )

        # Send the initial message
        await new_thread.send(message)

        return new_thread
