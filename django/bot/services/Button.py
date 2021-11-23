from os import sync

import discord
import emojis
from asgiref.sync import async_to_sync, sync_to_async

from bot.discord_models.models import Category, Channel, Guild, Role
from bot.services.Dropdown import Dropdown
from bot.users.models import Member
from currencies.models import Currency, Payment, Trade, Transaction
from currencies.services import (CreateBankEmbed, CreateTrade,
                                 CreateTradeEmbed, LockPayment)
from django.db import models, transaction
from players.models import Player
from responses.models import Response
from teams.models import Team

from .Payment import update_payment_view
from .TaskHandler import TaskHandler
from .Trade import TradeView


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

    async def adjust_currency_trade(self, interaction: discord.Interaction):
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

        # Get team interacting based on what channel the interaction is in
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

        # @transaction.atomic
        @sync_to_async
        def check_and_change(
            amount,
            interacting_team_wallet,
            interaction,
            currency,
            initiating_party_wallet,
            receiving_party_wallet,
            trade,
        ):
            # Make sure the from wallet has enough currency
            if amount > 0:
                bank_balance = interacting_team_wallet.get_bank_balance(new=True)

                if bank_balance[currency] < amount:
                    async_to_sync(interaction.response.send_message)(
                        content="You don't have enough {} to adjust the trade.".format(
                            currency.name
                        ),
                        ephemeral=True,
                    )
                    return

            from_wallet = interacting_team_wallet
            to_wallet = (
                initiating_party_wallet
                if initiating_party_wallet.id != from_wallet.id
                else receiving_party_wallet
            )

            transaction, _ = Transaction.objects.get_or_create(
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
                transaction.delete()
            else:
                trade.transactions.add(transaction)
                transaction.save()

        await check_and_change(
            amount,
            interacting_team_wallet,
            interaction,
            currency,
            initiating_party_wallet,
            receiving_party_wallet,
            trade,
        )

        trade.initiating_party_accepted = False
        trade.receiving_party_accepted = False

        await sync_to_async(trade.save)()

        handler = TaskHandler(discord.ui.View(timeout=None), self.client)
        trade_view = await sync_to_async(TradeView)(
            trade, interaction, handler, self.client
        )

        await sync_to_async(interacting_team.update_bank_embed)(self.client)

        await sync_to_async(trade_view.update_trade_view)()

    async def currency_trade_adjustment_menu(self, interaction: discord.Interaction):
        """When the "Adjust Trade Amounts" is clicked

        Creates a dropdown with all currencies for this team

        Args:
            interaction (discord.Interaction): The interaction object

        Payload:
            trade_id
            team_id
        """
        from .Dropdown import Dropdown

        trade_id = self.callback_payload["trade_id"]
        team_id = self.callback_payload["team_id"]

        # Get all currencies that a team has in their bank
        @sync_to_async
        def get_currencies(team_id):
            team: Team = Team.objects.get(id=team_id)

            currencies = team.wallet.get_currencies_available()
            currencies = [
                currency
                for currency in currencies
                if currency.currency_type in ["COM", "RAR"]
            ]

            return currencies

        currencies: list[Currency] = await get_currencies(team_id)

        # Collect all the currencies
        currency_options = []
        for currency in currencies:
            currency_options.append(
                discord.SelectOption(
                    label=currency.name,
                    value=currency.name,
                    emoji=emojis.encode(currency.emoji),
                )
            )

        handler = TaskHandler(discord.ui.View(timeout=None), self.client)

        await handler.create_dropdown_response(
            interaction=interaction,
            options=currency_options,
            max_values=1,
            do_next=Dropdown.adjustment_select_trade_currency.__name__,
            callback_payload={
                "guild_id": interaction.guild.id,
                "channel_id": interaction.channel_id,
                "trade_id": trade_id,
                "placeholder": "Select a currency",
            },
        )

    async def make_payment(self, interaction: discord.Interaction):
        """When the "Pay X" is clicked

        Adds a transaction to the payment for that team

        Args:
            interaction (discord.Interaction): The interaction object

        Payload:
            payment_id
            count
        """
        from .Dropdown import Dropdown

        payment_id = self.callback_payload["payment_id"]
        count = self.callback_payload["count"]

        # Get the team of the user that is interacting
        user_id = interaction.user.id

        # Use a class to get type hints across sync_to_async boundaries
        class PaymentSyncQuery:
            payment: Payment
            team: Team
            balance: list[Currency]
            megabucks: Currency
            player: Player

        # Get all currencies that a team has in their bank
        @sync_to_async
        def get_team(user_id, payment_id) -> PaymentSyncQuery:
            query = PaymentSyncQuery()

            query.payment = Payment.objects.get(id=payment_id)

            member: Member = Member.objects.get(discord_id=user_id)
            team: Team = member.player.team
            query.team = team

            query.player = member.player

            query.balance = team.wallet.get_bank_balance(new=True)

            query.megabucks = Currency.objects.get(name="Megabucks")

            return query

        query: PaymentSyncQuery = await get_team(user_id, payment_id)

        if query.payment.completed:
            await interaction.response.send_message(
                content="This payment has already been completed!",
                ephemeral=True,
            )
            return

        # Make sure the team has enough money to pay
        if (
            query.megabucks not in query.balance
            or query.balance[query.megabucks] < query.payment.cost * count
        ):
            await interaction.response.send_message(
                content="You don't have enough Megacredits to pay this payment!",
                ephemeral=True,
            )
            return

        # Lock the payment to the transaction
        @sync_to_async
        def create_transaction(query: PaymentSyncQuery):
            transaction = Transaction.objects.create(
                amount=query.payment.cost * count,
                currency=query.megabucks,
                from_wallet=query.team.wallet,
                # Send to the bank
                to_wallet=Team.objects.get(name="null").wallet,
                initiating_player=query.player,
            )

            query.payment.transactions.add(transaction)

            query.payment.save()

            # If this is a fundraiser
            if query.payment.fundraising_amount > 0:
                total = sum(
                    [
                        transaction.amount
                        for transaction in query.payment.transactions.all()
                    ]
                )

                if total >= query.payment.fundraising_amount:
                    transaction.amount -= total - query.payment.fundraising_amount
                    if transaction.amount <= 0:
                        transaction.delete()
                        return False
                    else:
                        transaction.save()

                    return True

            return False

        finished_fundraiser = await create_transaction(query)

        # Update the bank of the team that paid
        await sync_to_async(query.team.update_bank_embed)(self.client)

        if finished_fundraiser:
            await sync_to_async(LockPayment.execute)({"payment_id": payment_id})
            channel: discord.TextChannel = interaction.guild.get_channel_or_thread(
                query.payment.channel_id
            )

            message = await channel.fetch_message(query.payment.embed_id)
            await message.edit(embed=message.embeds[0], view=None)

        # Update the message
        await sync_to_async(update_payment_view)(query.payment, interaction)

    async def lock_payment(self, interaction: discord.Interaction):
        """When the "Lock Payment" is clicked

        Locks the payment to the transaction

        Args:
            interaction (discord.Interaction): The interaction object

        Payload:
            payment_id
        """
        # Make sure an admin clicked this
        if "admin" not in [role.name for role in interaction.user.roles]:
            await interaction.response.send_message(
                "❗ You are not an admin.",
                ephemeral=True,
            )
            return

        payment_id = self.callback_payload["payment_id"]

        payment: Payment = await sync_to_async(LockPayment.execute)(
            {"payment_id": payment_id}
        )

        @sync_to_async
        def cancel_transactions():
            for transaction in payment.transactions.all():
                transaction.cancel()
                transaction.save()

            for team in Team.objects.all():
                if team.name == "null":
                    continue

                team.update_bank_embed(self.client)

        # Check if this is a fundraiser
        if payment.fundraising_amount > 0:
            await cancel_transactions()
            embed = await sync_to_async(update_payment_view)(payment, interaction)

        channel: discord.TextChannel = interaction.guild.get_channel_or_thread(
            payment.channel_id
        )

        message = await channel.fetch_message(payment.embed_id)

        embed = message.embeds[0]

        await message.edit(embed=embed, view=None)

    async def currency_trade_currency_menu(self, interaction: discord.Interaction):
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
            interaction=interaction,
            options=options,
            do_next=Dropdown.adjustment_select_trade_currency.__name__,
            callback_payload={
                "trade_id": self.callback_payload["trade_id"],
                "placeholder": "Which country do you want to trade with?",
            },
        )

    # From the team menu, "Start Trading" was pushed
    async def start_trading(self, interaction: discord.Interaction):
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
            interaction=interaction,
            options=options,
            max_values=1,
            do_next=Dropdown.set_up_trade_prompt.__name__,
            callback_payload={
                "trade_id": trade.id,
                "placeholder": "Which country do you want to trade with?",
            },
        )

        await sync_to_async(trade.save)()

    # When toggle trade accept is pressed
    async def accept_trade(self, interaction: discord.Interaction):
        trade_id = self.callback_payload["trade_id"]

        trade: Trade = await sync_to_async(Trade.objects.get)(id=trade_id)

        # Update trade state
        await sync_to_async(trade.swap_views)()

        # Delete the current thread
        # await interaction.channel.delete()

        await sync_to_async(trade.save)()

        # pass off rest to trade function
        handler = TaskHandler(discord.ui.View(timeout=None), self.client)
        trade_view: TradeView = await sync_to_async(TradeView)(
            trade, interaction, handler, self.client
        )
        await sync_to_async(trade_view.update_trade_view)()

    # When cancel trade is pressed from either team
    async def cancel_trade(self, interaction: discord.Interaction):
        trade_id = self.callback_payload["trade_id"]

        trade: Trade = await sync_to_async(Trade.objects.get)(id=trade_id)

        # Update trade state
        await sync_to_async(trade.cancel)()

        # Delete the current thread
        # await interaction.channel.delete()

        await sync_to_async(trade.save)()

        # pass off rest to trade function
        handler = TaskHandler(discord.ui.View(timeout=None), self.client)
        trade_view: TradeView = await sync_to_async(TradeView)(
            trade, interaction, handler, self.client
        )
        await sync_to_async(trade_view.cancel_trade_view)()

    async def complete_trade(self, interaction: discord.Interaction):
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
            print("Closing", transaction.id)
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

        # Change the embeds on the menu channels
        @sync_to_async
        def update_embeds(trade: Trade, client: discord.Client):
            trade.initiating_party.update_bank_embed(client)
            trade.receiving_party.update_bank_embed(client)

        await update_embeds(trade, self.client)

        await interaction.channel.delete()

        # TODO: Lock down channel

    # When toggle trade accept is pressed
    async def confirm(self, interaction: discord.Interaction):
        success_callback = self.callback_payload["success_callback"]
        fail_callback = self.callback_payload["fail_callback"]

        # Make button
        handler = TaskHandler(discord.ui.View(timeout=None), self.client)
        button_message = await handler.create_button(
            {
                "content": "Are you sure?",
                # "guild_id": interaction.guild.id,
                # "channel_discord_id": interaction.channel.id,
                "callback_payload": {},
                "button_rows": [
                    [
                        {
                            "x": 0,
                            "y": 0,
                            "style": discord.ButtonStyle.success,
                            "disabled": False,
                            "label": "Accept",
                            # "custom_id": "confirm",
                            "emoji": "✅",
                            "do_next": Button.accept.__name__,
                            "callback_payload": success_callback,
                        },
                        {
                            "x": 1,
                            "y": 0,
                            "style": discord.ButtonStyle.danger,
                            "disabled": False,
                            "label": "Cancel",
                            # "custom_id": "cancel",
                            "emoji": "❌",
                            "do_next": Button.cancel.__name__,
                            "callback_payload": fail_callback,
                        },
                    ]
                ],
            },
            interaction,
        )

        print(f"id {button_message.id}")

    async def accept(self, interaction: discord.Interaction):
        print(self.callback_payload)
        self.do_next = self.callback_payload["do_next"]
        self.callback_payload = self.callback_payload["callback_payload"]

        # TODO: Pass original interaction or something

        await self.callback(interaction)
        print(interaction.message.id)
        await interaction.delete_original_message()

    async def cancel(self, interaction: discord.Interaction):
        self.do_next = self.callback_payload["do_next"]
        self.callback_payload = self.callback_payload["callback_payload"]

        await self.callback(interaction)
        await interaction.message.delete_original_message()

    async def open_comms(self, interaction: discord.Interaction):
        team_id = self.callback_payload["team_id"]

        @sync_to_async
        def get_sender_team(interaction, team_id):
            from teams.models import Team

            interacting_team = Team.objects.get(id=team_id)

            team_options = []
            for team in Team.objects.all():
                if not team.emoji or team.id == interacting_team.id:
                    continue

                team_options.append(
                    discord.SelectOption(
                        label=team.name,
                        description="",
                        emoji=emojis.encode(team.emoji),
                    )
                )

            return team_options, interacting_team

        (team_options, interacting_team) = await get_sender_team(interaction, team_id)

        handler = TaskHandler(discord.ui.View(timeout=None), self.client)
        await handler.create_dropdown_response(
            interaction=interaction,
            options=team_options,
            max_values=3,
            do_next=Dropdown.open_comms_channel.__name__,
            callback_payload={
                "placeholder": "Which countries do you want contact?",
                "interacting_team": interacting_team.id,
            },
        )

    async def update_bank(self, interaction: discord.Interaction):
        from teams.models import Team

        team_id = self.callback_payload["team_id"]

        team: Team = await sync_to_async(Team.objects.get)(id=team_id)

        await sync_to_async(team.update_bank_embed)(self.client)

    async def callback(self, interaction: discord.Interaction):
        # Use to tie the function name to the function
        # Can probably be done better
        function_lookup = {
            self.accept_trade.__name__: self.accept_trade,
            self.cancel_trade.__name__: self.cancel_trade,
            self.adjust_currency_trade.__name__: self.adjust_currency_trade,
            self.currency_trade_adjustment_menu.__name__: self.currency_trade_adjustment_menu,
            self.currency_trade_currency_menu.__name__: self.currency_trade_currency_menu,
            self.complete_trade.__name__: self.complete_trade,
            self.start_trading.__name__: self.start_trading,
            self.make_payment.__name__: self.make_payment,
            self.lock_payment.__name__: self.lock_payment,
            self.confirm.__name__: self.confirm,
            self.accept.__name__: self.accept,
            self.cancel.__name__: self.cancel,
            self.open_comms.__name__: self.open_comms,
            self.update_bank.__name__: self.update_bank,
        }

        await function_lookup[self.do_next](interaction)
