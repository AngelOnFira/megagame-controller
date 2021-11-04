import random

import emojis
from django_seed import Seed

from actions import watch_the_skies_data
from bot.accounts.models import User
from bot.discord_models.models import Category, Channel, Guild, Role
from bot.users.models import Member
from currencies.models import Currency, Trade, Transaction, Wallet
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
        Player.objects.all().delete()
        Transaction.objects.all().delete()
        Trade.objects.all().delete()  # requires transaction
        Team.objects.all().delete()  # requires trade
        Role.objects.all().delete()  # requires team
        Member.objects.all().delete()
        Task.objects.all().delete()
        Currency.objects.all().delete()
        Wallet.objects.all().delete()

        # Discord items
        Category.objects.all().delete()
        Channel.objects.all().delete()

        guild = Guild.objects.all().first()

        if len(User.objects.filter(username="f")) == 0:
            User.objects.create_superuser("f", "f@f.com", "password")

        # Create a category for the trades
        QueueTask.execute(
            {
                "task_type": TaskType.CREATE_CATEGORY,
                "payload": {
                    "category_name": "trades",
                    "guild_id": guild.discord_id,
                },
            }
        )

        seeder = Seed.seeder(locale="en_CA")

        emoji_list = ["💰", "🃏", "🛩️"]
        currencies = ["Credits", "Action card", "Interceptor"]

        for i in range(len(emoji_list)):
            seeder.add_entity(
                Currency,
                1,
                {
                    "name": currencies[i],
                    "emoji": emojis.decode(emoji_list[i]),
                },
            )

        emoji = seeder.execute()

        guild = Guild.objects.all().first()

        credits_currency = Currency.objects.get(name="Credits")
        bank_wallet = Wallet.objects.get_or_create(name="Bank")[0]

        for i, (team_name, team) in enumerate(watch_the_skies_data["teams"].items()):
            if i > 1:
                break

            seeder.add_entity(Wallet, 1, {"name": f"{team_name}'s wallet"})

            results = seeder.execute()

            team_wallet_id = results[Wallet][0]

            seeder.add_entity(
                Team,
                1,
                {
                    "name": team_name,
                    "emoji": emojis.decode(team["flag"]),
                    "wallet": Wallet.objects.get(id=team_wallet_id),
                    "guild": guild,
                },
            )

            # Pay each country their income
            seeder.add_entity(
                Transaction,
                1,
                {
                    "amount": team["income_track"][5],
                    "currency": credits_currency,
                    "from_wallet": bank_wallet,
                    "to_wallet": Wallet.objects.get(id=team_wallet_id),
                    "state": "completed",
                },
            )

            seeder.execute()

        print("Seeding Complete")
