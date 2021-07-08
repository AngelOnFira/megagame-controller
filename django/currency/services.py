from django import forms
from service_objects.services import Service
from .models import Wallet, Transaction, Currency


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

        wallet = Wallet.objects.get(pk=destination_wallet)
        currency = Currency.objects.get(name=currency_name)

        transaction = Transaction.objects.create(
            amount=amount, wallet=wallet, currency=currency
        )

        transaction.create()
        transaction.save()

        wallet = Wallet.objects.get(pk=destination_wallet)
        wallet

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

        self.currency = Currency.objects.get_or_create(
            name=name,
            description=description,
        )

        return self.currency
