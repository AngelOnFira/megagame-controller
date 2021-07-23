import random
from django.core.management.base import BaseCommand
from django_seed import Seed
from django.conf import settings

from player.models import Player
from currency.models import Currency, Transaction, Wallet
from tasks.models import Task
from team.models import Team
from bot.plugins.stats.models import LoggedMessage


class Command(BaseCommand):
    help = "Seed the database with fake players"

    def handle(self, *args, **kwargs):
        # Make sure we are in debug mode
        if settings.DEBUG != True:
            return

        # LoggedMessage.objects.all().delete()
        # Player.objects.all().delete()
        # Team.objects.all().delete()
        # Transaction.objects.all().delete()
        # Currency.objects.all().delete()
        # Wallet.objects.all().delete()

        seeder = Seed.seeder(locale="en_CA")

        # # Add a wallet
        # seeder.add_entity(Wallet, 3)

        # for name in ["FirstPlayer", "SecondPlayer", "ThirdPlayer"]:
        #     seeder.add_entity(
        #         Player,
        #         1,
        #         {
        #             "name": name,
        #         },
        #     )

        player = Player.objects.get(id=9)

        seeder.add_entity(Task, 10, {"player": player, "completed": False})

        seeder.execute()

        print("Seeding Complete")
