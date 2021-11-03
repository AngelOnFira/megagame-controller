import discord
import emojis
from asgiref.sync import sync_to_async

from bot.discord_models.models import Category, Channel, Guild, Role
from bot.services.Dropdown import Dropdown
from bot.users.models import Member
from currencies.models import Currency, Trade, Transaction
from currencies.services import CreateBankEmbed, CreateTrade, CreateTradeEmbed
from players.models import Player
from responses.models import Response
from teams.models import Team

from .TaskHandler import TaskHandler
from .Trade import update_trade_view


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
            do_next=Dropdown.adjustment_select_trade_currency.__name__,
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
            do_next=Button.accept_trade.__name__,
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
            do_next=Button.lock_in_trade.__name__,
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

        embed = await sync_to_async(CreateTradeEmbed.execute)({"trade_id": trade_id})

        message: discord.Message = await interaction.channel.fetch_message(
            trade.embed_id
        )

        view = await trade_view(self.client, trade)

        await message.edit(embed=embed, view=view)

    async def currency_trade_adjustment_menu(self, interaction: discord.Interaction):
        # payload: expect a currency id
        # TODO: change to only currencies that a team has in their bank
        currencies: Currency = await sync_to_async(list)(Currency.objects.all())

        button_rows = []

        currency: Currency
        for i, currency in enumerate(currencies):
            row = []

            for j, label in enumerate(["-5", "-1", "+1", "+5"]):
                style = (
                    discord.ButtonStyle.danger if j < 2 else discord.ButtonStyle.success
                )

                value_button = {
                    "x": j,
                    "y": i,
                    "style": style,
                    "disabled": False,
                    "label": label,
                    "custom_id": f"{currency.id}|{self.callback_payload['trade_id']}|{label}",
                    "do_next": Button.adjust_currency_trade.__name__,
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

        # update trade state
        trade.initiating_party_accept()

        # Delete the current thread
        await interaction.channel.delete()

        await sync_to_async(trade.save)()

        # pass off rest to trade function
        handler = TaskHandler(discord.ui.View(timeout=None), self.client)
        update_trade_view(handler, trade, interaction)

    async def lock_in_trade(self, interaction: discord.Interaction):
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

    async def callback(self, interaction: discord.Interaction):
        # Use to tie the function name to the function
        # Can probably be done better
        function_lookup = {
            self.accept_trade.__name__: self.accept_trade,
            self.adjust_currency_trade.__name__: self.adjust_currency_trade,
            self.currency_trade_adjustment_menu.__name__: self.currency_trade_adjustment_menu,
            self.currency_trade_currency_menu.__name__: self.currency_trade_currency_menu,
            self.lock_in_trade.__name__: self.lock_in_trade,
            self.start_trading.__name__: self.start_trading,
        }

        await function_lookup[self.do_next](interaction)
