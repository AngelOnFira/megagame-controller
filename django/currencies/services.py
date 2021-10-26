import json
from collections import defaultdict
from pydoc import describe

import discord
import emojis
from bot.users.models import Member
from service_objects.fields import DictField, ListField, ModelField
from service_objects.services import Service
from tasks.models import TaskType
from tasks.services import QueueTask
from teams.models import Team

from django import forms

from .models import Currency, Trade, Transaction, Wallet


class CreateTradeEmbed(Service):
    trade_id = forms.IntegerField()

    def process(self):
        trade_id = self.cleaned_data["trade_id"]

        trade = Trade.objects.get(id=trade_id)

        embed: discord.Embed = discord.Embed(
            title=f"Trade for {trade.initiating_party.name} & {trade.receiving_party.name}"
        )

        # Build recipt for initiating party
        initiating_party_transactions = ""
        for transaction in Transaction.objects.filter(
            trade=trade, from_wallet=trade.initiating_party.wallet
        ):
            initiating_party_transactions += (
                f"{transaction.amount} {transaction.currency.name}\n"
            )
        if initiating_party_transactions == "":
            initiating_party_transactions = "-"

        # Build recipt for receiving party
        receiving_party_transactions = ""
        for transaction in Transaction.objects.filter(
            trade=trade, from_wallet=trade.receiving_party.wallet
        ):
            receiving_party_transactions += (
                f"{transaction.amount} {transaction.currency.name}\n"
            )
        if receiving_party_transactions == "":
            receiving_party_transactions = "-"

        # Count the number of newlines in the transaction strings
        init_newline_count = initiating_party_transactions.count("\n")
        recv_newline_count = receiving_party_transactions.count("\n")

        num_newlines = max(init_newline_count, recv_newline_count)

        # Add extra newlines to the shorter string (ty copilot)
        if init_newline_count < recv_newline_count:
            initiating_party_transactions += "\n" * (num_newlines - init_newline_count)
        elif init_newline_count > recv_newline_count:
            receiving_party_transactions += "\n" * (num_newlines - recv_newline_count)

        # Create embed for each team
        initiating_party_transactions += "\n\nAccepted: " + (
            "✅" if trade.initiating_party_accepted else "❌" + "\n"
        )
        embed.add_field(
            name=trade.initiating_party.name,
            value=initiating_party_transactions,
        )

        receiving_party_transactions += "\n\nAccepted: " + (
            "✅" if trade.receiving_party_accepted else "❌" + "\n"
        )
        embed.add_field(
            name=trade.receiving_party.name,
            value=receiving_party_transactions,
        )

        embed.add_field(
            name="|",
            value="|\n" * (num_newlines + 4),
        )

        description = """
            *Once both teams have accepted, either team
            can lock in the trade. Any changes to the
            amounts will turn off accepted for both teams*
            """

        embed.add_field(
            name="Details",
            value=description,
        )

        return embed


from collections import defaultdict


class CreateBankEmbed(Service):
    team_id = forms.IntegerField()

    def process(self):
        team_id = self.cleaned_data["team_id"]

        team = Team.objects.get(id=team_id)

        transaction_totals = defaultdict(int)

        for credit in team.wallet.credits.filter(state="completed"):
            transaction_totals[credit.currency.name] -= credit.amount

        for debit in team.wallet.debits.filter(state="completed"):
            transaction_totals[debit.currency.name] += debit.amount

        print(transaction_totals)

        text = ""

        for currency, amount in transaction_totals.items():
            text += f"{amount} {currency}\n"

        embed: discord.Embed = discord.Embed(
            title=f"Bank of {team.name}", description=text
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
    initiating_team = ModelField(Team)
    team_lookup = DictField()

    def process(self):
        initiating_team = self.cleaned_data["initiating_team"]
        team_lookup = self.cleaned_data["team_lookup"]

        trade = Trade.objects.create(
            initiating_party=initiating_team,
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
