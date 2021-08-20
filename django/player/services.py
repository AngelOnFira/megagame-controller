from service_objects.services import Service

from currency.services import CreateWallet
from django import forms

from .models import Player


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
