from django import forms
from service_objects.services import Service

from .models import Currency, Transaction, Wallet
from team.models import Team
from bot.users.models import Member


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


class CreateTransaction(Service):
    message_id = forms.IntegerField()
    message_sender_id = forms.IntegerField()

    def process(self):
        message_id = self.cleaned_data["message_id"]
        message_sender_id = self.cleaned_data["message_sender_id"]

        player_team = Member.objects.get(id=message_sender_id).player.team

        transaction = Transaction.objects.create(
            current_message_id=message_id, from_wallet=player_team.wallet
        )

        transaction.create()
        transaction.save()

        return transaction


class UpdateTransaction(Service):
    message_id = forms.IntegerField()
    team_emoji = forms.CharField()

    def process(self):
        message_id = self.cleaned_data["message_id"]
        team_emoji = self.cleaned_data["team_emoji"]

        transaction = Transaction.objects.get(current_message_id=message_id)

        if transaction.state == "created":
            team = Team.objects.get(emoji=team_emoji)
            transaction.to_wallet = team.wallet
            transaction.set_destination()
            transaction.save()

        elif transaction.state == "destination_set":
            transaction.state = "completed"
            transaction.set_currency()
            transaction.save()

        transaction.create()
        transaction.save()

        return transaction


class TransactionBegin(Service):
    message_id = forms.IntegerField()

    def process(self):
        message_id = self.cleaned_data["message_id"]

        transaction = Transaction.objects.create(current_message_id=message_id)

        transaction.create()
        transaction.save()

        return transaction


class TransactionDestination(Service):
    team_emoji = forms.CharField()
    message_id = forms.IntegerField()

    def process(self):
        currency_name = self.cleaned_data["currency_name"]
        amount = self.cleaned_data["amount"]
        destination_wallet = self.cleaned_data["destination_wallet"]

        wallet = Wallet.objects.get(
            pk=Member.objects.get(name="AngelOnFira").player.wallet.id
        )
        print(wallet)
        bank, created = Wallet.objects.get_or_create(name="Bank")
        currency = Currency.objects.get(name=currency_name)
        # wallet = Wallet.objects.get(pk=destination_wallet)

        transaction = Transaction.objects.create(
            amount=amount, from_wallet=bank, to_wallet=wallet, currency=currency
        )

        transaction.create()
        transaction.save()

        return transaction


class TransactionCurrency(Service):
    currency_emoji = forms.CharField()
    message_id = forms.IntegerField()

    def process(self):
        currency_name = self.cleaned_data["currency_name"]
        amount = self.cleaned_data["amount"]
        destination_wallet = self.cleaned_data["destination_wallet"]

        wallet = Wallet.objects.get(
            pk=Member.objects.get(name="AngelOnFira").player.wallet.id
        )
        print(wallet)
        bank, created = Wallet.objects.get_or_create(name="Bank")
        currency = Currency.objects.get(name=currency_name)
        # wallet = Wallet.objects.get(pk=destination_wallet)

        transaction = Transaction.objects.create(
            amount=amount, from_wallet=bank, to_wallet=wallet, currency=currency
        )

        transaction.create()
        transaction.save()

        return transaction


class TransactionAmount(Service):
    currency_name = forms.CharField()
    amount = forms.DecimalField()
    destination_wallet = forms.IntegerField()
    message_id = forms.IntegerField()

    def process(self):
        currency_name = self.cleaned_data["currency_name"]
        amount = self.cleaned_data["amount"]
        destination_wallet = self.cleaned_data["destination_wallet"]

        wallet = Wallet.objects.get(
            pk=Member.objects.get(name="AngelOnFira").player.wallet.id
        )
        print(wallet)
        bank, created = Wallet.objects.get_or_create(name="Bank")
        currency = Currency.objects.get(name=currency_name)
        # wallet = Wallet.objects.get(pk=destination_wallet)

        transaction = Transaction.objects.create(
            amount=amount, from_wallet=bank, to_wallet=wallet, currency=currency
        )

        transaction.create()
        transaction.save()

        return transaction


class CompleteTransaction(Service):
    transaction_id = forms.IntegerField()

    def process(self):
        transaction_id = self.cleaned_data["transaction_id"]

        transaction = Transaction.objects.get(id=transaction_id)

        transaction.complete()
        transaction.save()

        return transaction
