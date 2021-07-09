from django import forms
from service_objects.services import Service

from .models import Currency, Transaction, Wallet
from bot.users.models import Member


class CreateWallet(Service):
    def process(self):

        self.wallet = Wallet.objects.create(name="Player wallet")

        return self.wallet


class CreateTransaction(Service):
    currency_name = forms.CharField()
    amount = forms.DecimalField()
    destination_wallet = forms.IntegerField()

    def process(self):
        currency_name = self.cleaned_data["currency_name"]
        amount = self.cleaned_data["amount"]
        destination_wallet = self.cleaned_data["destination_wallet"]

        wallet = Wallet.objects.get(pk=Member.objects.get(name="AngelOnFira").player.wallet.id)
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
