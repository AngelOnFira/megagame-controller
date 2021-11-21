from service_objects.services import Service

from currencies.models import Currency, Transaction, Wallet
from django import forms

from .models import Team

# class CreateWallet(Service):
#     def process(self):

#         self.wallet = Wallet.objects.create(name="Player wallet")

#         return self.wallet


class GlobalTurnChange(Service):
    advance = forms.BooleanField()

    def process(self):
        advance = self.cleaned_data["advance"]

        megabucks = Currency.objects.get(name="Megabucks")
        bank_wallet = Wallet.objects.get_or_create(name="Bank")[0]

        # Go through each team
        team: Team
        for team in Team.objects.all():
            if team.name == "null":
                continue

            income = team.get_income()

            # Either send to team or to bank
            if advance:
                Transaction.objects.create(
                    amount=income,
                    currency=megabucks,
                    from_wallet=bank_wallet,
                    to_wallet=team.wallet,
                    state="completed",
                )
            else:
                Transaction.objects.create(
                    amount=income,
                    currency=megabucks,
                    from_wallet=team.wallet,
                    to_wallet=bank_wallet,
                    state="completed",
                )
