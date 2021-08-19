import random
from django.core.management.base import BaseCommand
from django_seed import Seed
from django.conf import settings

from player.models import Player
from currency.models import Currency, Transaction, Wallet
from tasks.models import Task
from team.models import Team
from bot.plugins.stats.models import LoggedMessage
from currency.models import Currency
from id_emojis.models import IDEmoji
import emojis
from bot.users.models import Member
from tasks.models import Task
from bot.discord_guilds.models import Guild


class Command(BaseCommand):
    help = "Seed the database with fake players"

    def handle(self, *args, **kwargs):
        # Make sure we are in debug mode
        if settings.DEBUG != True:
            return

        # LoggedMessage.objects.all().delete()
        Player.objects.all().delete()
        Member.objects.all().delete()
        Team.objects.all().delete()
        # Transaction.objects.all().delete()
        Task.objects.all().delete()
        Currency.objects.all().delete()
        IDEmoji.objects.all().delete()
        Wallet.objects.all().delete()

        # Wallet.objects.all().delete()

        seeder = Seed.seeder(locale="en_CA")

        emoji_list = ["💰", "🃏", "🛩️"]
        currencies = ["Credits", "Action card", "Interceptor"]

        for i in range(len(emoji_list)):

            seeder.add_entity(
                IDEmoji,
                1,
                {
                    "emoji": emoji_list[i],
                    "emoji_text": emojis.decode(emoji_list[i]),
                },
            )

            emoji = seeder.execute()

            seeder.add_entity(
                Currency,
                1,
                {
                    "name": currencies[i],
                    "emoji": IDEmoji.objects.get(id=emoji[IDEmoji][0]),
                },
            )

            emoji = seeder.execute()

        guild = Guild.objects.all().first()
        emoji_list = ["🇨🇦", "🇬🇧", "🇺🇸", "🇫🇷", "🇩🇪", "🇮🇹"]
        emoji_names = [":canada:", ":uk:", ":us:", ":france:", ":de:", ":italy:"]
        country_names = [
            "Canada",
            "United Kingdom",
            "United States",
            "France",
            "Germany",
            "Italy",
        ]

        for i in range(len(emoji_list)):
            seeder.add_entity(
                IDEmoji,
                1,
                {
                    "emoji": emoji_list[i],
                    "emoji_text": emoji_names[i],
                },
            )

            seeder.add_entity(Wallet, 1, {"name": f"{country_names[i]}'s wallet"})

            results = seeder.execute()

            seeder.add_entity(
                Team,
                1,
                {
                    "name": country_names[i],
                    "emoji": IDEmoji.objects.get(id=results[IDEmoji][0]),
                    "wallet": Wallet.objects.get(id=results[Wallet][0]),
                    "guild": guild,
                },
            )

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

        # player = Player.objects.get(id=9)

        # seeder.add_entity(Task, 10, {"player": player, "completed": False})

        # seeder.execute()

        print("Seeding Complete")
