from django import forms
from service_objects.services import Service
from .models import Player
from currency.services import CreateWallet, CreateTransaction, CreateCurrency


class CreatePlayer(Service):
    def process(self):
        wallet = CreateWallet.execute({})

        # initial_transition = CreateTransaction.execute(
        #     {
        #         "currency_name": credits.name,
        #         "amount": 100,
        #         "destination_wallet": wallet.id,
        #     }
        # )

        player = Player.objects.create(wallet=wallet)

        return player
