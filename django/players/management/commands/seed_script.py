import random

import emojis
from django_seed import Seed

from actions import watch_the_stars_data
from bot.accounts.models import User
from bot.discord_models.models import Category, Channel, Guild, Role
from bot.users.models import Member
from currencies.models import Currency, Payment, Trade, Transaction, Wallet
from django.conf import settings
from django.core.management.base import BaseCommand
from players.models import Player
from tasks.models import Task, TaskType
from tasks.services import QueueTask
from teams.models import Team


class Command(BaseCommand):
    help = "Seed the database with fake players"

    def handle(self, *args, **kwargs):
        # Make sure we are in debug mode
        if settings.DEBUG != True:
            return

        # LoggedMessage.objects.all().delete()
        Trade.objects.all().delete()  # requires transaction
        Transaction.objects.all().delete()
        Wallet.objects.all().delete()
        Player.objects.all().delete()
        Team.objects.all().delete()  # requires trade
        Role.objects.all().delete()  # requires team
        Member.objects.all().delete()
        Task.objects.all().delete()
        Currency.objects.all().delete()
        Payment.objects.all().delete()

        # Discord items
        Category.objects.all().delete()
        Channel.objects.all().delete()

        guild = Guild.objects.all().first()

        if len(User.objects.filter(username="f")) == 0:
            User.objects.create_superuser("f", "f@f.com", "password")

        # # Create a category for the admin game channels
        # QueueTask.execute(
        #     {
        #         "task_type": TaskType.CREATE_CATEGORY,
        #         "payload": {
        #             "category_name": "admin",
        #             "guild_id": guild.discord_id,
        #         },
        #     }
        # )

        # # Create a category for the general game channels
        QueueTask.execute(
            {
                "task_type": TaskType.CREATE_CATEGORY,
                "payload": {
                    "category_name": "earth",
                    "guild_id": guild.discord_id,
                },
            }
        )

        # Create a category for the trades
        QueueTask.execute(
            {
                "task_type": TaskType.CREATE_CATEGORY,
                "payload": {
                    "category_name": "comms",
                    "guild_id": guild.discord_id,
                },
            }
        )

        seeder = Seed.seeder(locale="en_CA")

        for currency_type in watch_the_stars_data["currencies"].keys():
            for currency in watch_the_stars_data["currencies"][currency_type]:
                Currency.objects.create(
                    name=currency[0],
                    emoji=emojis.decode(currency[1]),
                    currency_type={
                        "admin": "ADM",
                        "common": "COM",
                        "rare": "RAR",
                        "logistics": "LOG",
                        "hidden": "HID",
                        "special": "SPE",
                    }[currency_type],
                )

        guild = Guild.objects.all().first()

        bank_wallet = Wallet.objects.get_or_create(name="Bank")[0]

        currency_lookup = {}
        for currency in Currency.objects.all():
            currency_lookup[currency.name] = currency

        for i, (team_name, team) in enumerate(watch_the_stars_data["teams"].items()):
            # if i > 1:
            #     break

            wallet = Wallet.objects.create(
                name=f"{team_name}'s wallet",
            )

            team_wallet_id = wallet.id

            Team.objects.create(
                name=team_name,
                abreviation=team["abreviation"],
                emoji=emojis.decode(team["flag"]),
                wallet=Wallet.objects.get(id=team_wallet_id),
                guild=guild,
            )

            # Set up each country's initial currencies
            for currency_name, currency_amount in team["initial_currencies"]:
                Transaction.objects.create(
                    amount=currency_amount,
                    currency=currency_lookup[currency_name],
                    from_wallet=bank_wallet,
                    to_wallet=Wallet.objects.get(id=team_wallet_id),
                    state="completed",
                )

            random_list = [
                "Dead Alien",
                "Saucer Wreck",
                "Exotic Materials",
                "Unidentified Alien Items",
                "Live Alien",
                "Alien Entertainment System",
                "Alien Personal Weapons",
                "Alien Power Generator",
                "Alien Energy Crystals",
                "Alien Foods",
                "Alien Communications System",
                "Alien Computer",
            ]

            for i in range(4):
                Transaction.objects.create(
                    amount=1,
                    currency=Currency.objects.get(name=random.choice(random_list)),
                    from_wallet=bank_wallet,
                    to_wallet=Wallet.objects.get(id=team_wallet_id),
                    state="completed",
                )

            # Pay each country their income
            Transaction.objects.create(
                amount=team["income_track"][5],
                currency=currency_lookup["Megabucks"],
                from_wallet=bank_wallet,
                to_wallet=Wallet.objects.get(id=team_wallet_id),
                state="completed",
            )

        print("Seeding Complete")
