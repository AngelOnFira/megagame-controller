import json

import discord
import emojis
from service_objects.fields import DictField, ListField, ModelField
from service_objects.services import Service

from bot.users.models import Member
from django import forms
from tasks.models import TaskType
from tasks.services import QueueTask
from teams.models import Team

from .models import Currency, Trade, Transaction, Wallet


class CreateTradeEmbed(Service):
    trade = ModelField(Trade)

    def process(self):
        trade: Trade = self.cleaned_data["trade"]

        embed = discord.Embed(
            title=f"Trade for {trade.initiating_party.name} & {trade.receiving_party.name}"
        )

        initiating_party_transactions = ""

        for transaction in Transaction.objects.filter(
            trade=trade, from_wallet=trade.initiating_party.wallet
        ):
            initiating_party_transactions += (
                f"{transaction.amount} {transaction.currency.name}\n"
            )

        embed.add_field(
            name="Initiating Party",
            value=f"{trade.initiating_party.name}\n{initiating_party_transactions}",
        )

        receiving_party_transactions = ""

        for transaction in Transaction.objects.filter(
            trade=trade, from_wallet=trade.receiving_party.wallet
        ):
            receiving_party_transactions += (
                f"{transaction.amount} {transaction.currency.name}\n"
            )

        embed.add_field(
            name="Receiving Party",
            value=f"{trade.receiving_party.name}\n{receiving_party_transactions}",
        )

        return embed


class CreateWallet(Service):
    def process(self):

        self.wallet = Wallet.objects.create(name="Player wallet")

        return self.wallet


class CreateCurrency(Service):
    name = forms.CharField()
    description = forms.CharField()

    def process(self):
        name = self.cleaned_data["name"]
        description = self.cleaned_data["description"]

        currency, created = Currency.objects.get_or_create(
            name=name,
            description=description,
        )

        return currency


class CreateTrade(Service):
    message_sender_id = forms.CharField()
    team_lookup = DictField()

    def process(self):
        message_sender_id = self.cleaned_data["message_sender_id"]
        team_lookup = self.cleaned_data["team_lookup"]

        player_team = Member.objects.get(discord_id=message_sender_id).player.team

        trade = Trade.objects.create(
            initiating_party=player_team,
            team_lookup=team_lookup,
        )

        return trade


class SelectTradeReceiver(Service):
    payload = DictField()
    values = ListField()

    def process(self):
        payload = self.cleaned_data["payload"]
        values = self.cleaned_data["values"]

        trade: Trade = Trade.objects.get(id=payload["trade_id"])

        trade.set_receiver(values)
        trade.save()

        # QueueTask.execute(
        #         {
        #             "task_type": TaskType.CREATE_DROPDOWN,
        #             "payload": {
        #                 "guild_id": message.guild.id,
        #                 "channel_id": message.channel.id,
        #                 "do_next": {
        #                     "type": TaskType.TRADE_SELECT_RECEIVER,
        #                     "payload": {
        #                         "trade_id": trade.id,
        #                     },
        #                 },
        #                 "dropdown": {
        #                     "placeholder": "Which country do you want to trade with?",
        #                     "min_values": 1,
        #                     "max_values": 1,
        #                     "options": options,
        #                 },
        #             },
        #         }
        #     )

        # create channel for the trade
        # create table of items to trade

        # # TODO: Return error
        # if reaction_emoji not in trade.emoji_lookup:
        #     pass

        # if transaction.state == "created":
        #     team = Team.objects.get(emoji=reaction_emoji)
        #     transaction.to_wallet = team.wallet
        #     transaction.save()

        #     currency_text = "What currency would you like to trade?\n\n"
        #     emoji_lookup = {}

        #     for currency in Currency.objects.all().order_by("name"):
        #         currency_text += f"{currency.name}: {emojis.encode(currency.emoji)}\n"
        #         emoji_lookup[currency.emoji] = currency.id

        #     transaction.emoji_lookup = emoji_lookup

        #     return (currency_text, emoji_lookup)

        # elif transaction.state == "destination_set":
        #     transaction.state = "completed"
        #     transaction.set_currency()
        #     transaction.save()

        # return (None, None)


# class TransactionBegin(Service):
#     message_id = forms.IntegerField()

#     def process(self):
#         message_id = self.cleaned_data["message_id"]

#         transaction = Transaction.objects.create(current_message_id=message_id)

#         transaction.create()
#         transaction.save()

#         return transaction


# class TransactionDestination(Service):
#     team_emoji = forms.CharField()
#     message_id = forms.IntegerField()

#     def process(self):
#         currency_name = self.cleaned_data["currency_name"]
#         amount = self.cleaned_data["amount"]
#         destination_wallet = self.cleaned_data["destination_wallet"]

#         wallet = Wallet.objects.get(
#             pk=Member.objects.get(name="AngelOnFira").player.wallet.id
#         )
#         print(wallet)
#         bank, created = Wallet.objects.get_or_create(name="Bank")
#         currency = Currency.objects.get(name=currency_name)
#         # wallet = Wallet.objects.get(pk=destination_wallet)

#         transaction = Transaction.objects.create(
#             amount=amount, from_wallet=bank, to_wallet=wallet, currency=currency
#         )

#         transaction.create()
#         transaction.save()

#         return transaction


# class TransactionCurrency(Service):
#     currency_emoji = forms.CharField()
#     message_id = forms.IntegerField()

#     def process(self):
#         currency_name = self.cleaned_data["currency_name"]
#         amount = self.cleaned_data["amount"]
#         destination_wallet = self.cleaned_data["destination_wallet"]

#         wallet = Wallet.objects.get(
#             pk=Member.objects.get(name="AngelOnFira").player.wallet.id
#         )
#         print(wallet)
#         bank, created = Wallet.objects.get_or_create(name="Bank")
#         currency = Currency.objects.get(name=currency_name)
#         # wallet = Wallet.objects.get(pk=destination_wallet)

#         transaction = Transaction.objects.create(
#             amount=amount, from_wallet=bank, to_wallet=wallet, currency=currency
#         )

#         transaction.create()
#         transaction.save()

#         return transaction


# class TransactionAmount(Service):
#     currency_name = forms.CharField()
#     amount = forms.DecimalField()
#     destination_wallet = forms.IntegerField()
#     message_id = forms.IntegerField()

#     def process(self):
#         currency_name = self.cleaned_data["currency_name"]
#         amount = self.cleaned_data["amount"]
#         destination_wallet = self.cleaned_data["destination_wallet"]

#         wallet = Wallet.objects.get(
#             pk=Member.objects.get(name="AngelOnFira").player.wallet.id
#         )
#         print(wallet)
#         bank, created = Wallet.objects.get_or_create(name="Bank")
#         currency = Currency.objects.get(name=currency_name)
#         # wallet = Wallet.objects.get(pk=destination_wallet)

#         transaction = Transaction.objects.create(
#             amount=amount, from_wallet=bank, to_wallet=wallet, currency=currency
#         )

#         transaction.create()
#         transaction.save()

#         return transaction


# class CompleteTransaction(Service):
#     transaction_id = forms.IntegerField()

#     def process(self):
#         transaction_id = self.cleaned_data["transaction_id"]

#         transaction = Transaction.objects.get(id=transaction_id)

#         transaction.complete()
#         transaction.save()

#         return transaction
