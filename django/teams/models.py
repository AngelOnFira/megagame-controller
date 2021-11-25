import json
from collections import defaultdict

import discord
import emojis
from asgiref.sync import async_to_sync

from actions import watch_the_stars_data
from bot.discord_models.models import Channel, Guild, Role
from currencies.models import Wallet
from django.db import models
from django.db.models.signals import post_save
from tasks.models import TaskType
from tasks.services import QueueTask


# Create your models here.
class Team(models.Model):
    name = models.CharField(max_length=100, unique=True)
    abreviation = models.CharField(max_length=2, null=True, blank=True)

    description = models.TextField(blank=True)
    guild = models.ForeignKey(
        "discord_models.Guild", on_delete=models.CASCADE, null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    emoji = models.CharField(max_length=30, blank=True, null=True)

    wallet: Wallet = models.OneToOneField(
        "currencies.Wallet",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="team",
    )

    role = models.OneToOneField(
        "discord_models.Role", on_delete=models.CASCADE, null=True, blank=True
    )

    category = models.OneToOneField(
        "discord_models.Category", on_delete=models.CASCADE, null=True, blank=True
    )

    # admin_channel = models.OneToOneField(
    #     "discord_models.Channel",
    #     on_delete=models.CASCADE,
    #     null=True,
    #     blank=True,
    #     related_name="team_admin_channel",
    # )

    general_channel = models.OneToOneField(
        "discord_models.Channel",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="team_general_channel",
    )

    trade_channel = models.OneToOneField(
        "discord_models.Channel",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="team_trade_channel",
    )

    menu_channel = models.OneToOneField(
        "discord_models.Channel",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="team_menu_channel",
    )

    bank_embed_id = models.BigIntegerField(null=True, blank=True, default=0)

    def __str__(self):
        # balance = self.get_bank_balance()
        # balance_string = ""

        # for currency, amount in balance.items():
        #     balance_string += f"{amount} {emojis.get(currency)} "
        # print(balance_string)

        if self.emoji:
            return f"{self.name} {emojis.decode(self.emoji)} ({self.id})"

        return f"{self.name} ({self.id})"

    def get_income_track(self):
        return watch_the_stars_data["teams"][self.name]["income_track"]

    def get_income(self):
        from currencies.models import Currency

        return self.get_income_track()[  # look on the income track
            self.wallet.get_bank_balance()[
                Currency.objects.get(name="Public Relations")  # get the PR of this team
            ]
        ]

    def update_bank_embed(self, client: discord.Client):
        if self.name == "null":
            return
            
        from currencies.services import CreateBankEmbed

        embed: discord.Embed = CreateBankEmbed.execute({"team_id": self.id})

        guild: discord.Guild = client.get_guild(self.guild.discord_id)
        channel: discord.TextChannel = guild.get_channel(self.menu_channel.discord_id)
        message: discord.Message = async_to_sync(channel.fetch_message)(
            self.bank_embed_id
        )

        async_to_sync(message.edit)(embed=embed)

    def refresh_team(self, client: discord.Client):
        # Kill all trades
        from currencies.models import Trade

        trades = Trade.objects.filter(initiating_party=self, state__in=["new"])
        for trade in trades:
            trade.cancel()
            trade.save()

        # Delete all the channels
        guild: discord.Guild = client.get_guild(self.guild.discord_id)

        menu_channel: discord.TextChannel = guild.get_channel(
            self.menu_channel.discord_id
        )
        async_to_sync(menu_channel.delete)()
        self.menu_channel.delete()
        self.menu_channel = None

        trade_channel: discord.TextChannel = guild.get_channel(
            self.trade_channel.discord_id
        )
        async_to_sync(trade_channel.delete)()
        self.trade_channel.delete()
        self.trade_channel = None

        self.save()

        # Delete active trades

        # Delete active transactions

    def create_team_ephemeral_channels(self):
        # Create a menu channel for the team
        name_altered = self.name.lower().replace(" ", "-")
        menu_channel = Channel.objects.create(
            guild=self.guild, name=f"{name_altered}-menu"
        )
        self.menu_channel = menu_channel
        self.save()
        QueueTask.execute(
            {
                "task_type": TaskType.CREATE_TEAM_CHANNEL,
                "payload": {
                    "team_id": self.id,
                    "channel_bind_model_id": menu_channel.id,
                    "type": False,
                },
            }
        )

        # Create a trade channel for the team
        trade_channel = Channel.objects.create(
            guild=self.guild, name=f"{name_altered}-trade"
        )
        self.trade_channel = trade_channel
        self.save()
        QueueTask.execute(
            {
                "task_type": TaskType.CREATE_TEAM_CHANNEL,
                "payload": {
                    "team_id": self.id,
                    "channel_bind_model_id": trade_channel.id,
                    "type": False,
                },
            }
        )

        # Add bank message
        QueueTask.execute(
            {
                "task_type": TaskType.CREATE_MESSAGE,
                "payload": {
                    "channel_id": self.menu_channel.id,
                    "message": "team_bank_embed",
                    "team_id": self.id,
                },
            }
        )

        from bot.services.Button import Button

        # Add bank message
        button_rows = [
            [
                {
                    "x": 0,
                    "y": 0,
                    "style": discord.ButtonStyle.primary,
                    "disabled": False,
                    "label": "Start Trade",
                    # "custom_id": f"{self.id}",
                    "emoji": "💱",
                    "do_next": Button.start_trading.__name__,
                    "callback_payload": {},
                },
                {
                    "x": 1,
                    "y": 0,
                    "style": discord.ButtonStyle.primary,
                    "disabled": False,
                    "label": "Open Comms",
                    # "custom_id": f"{self.id}-discuss",
                    "emoji": "💬",
                    "do_next": Button.open_comms.__name__,
                    "callback_payload": {
                        "team_id": self.id,
                    },
                },
                {
                    "x": 2,
                    "y": 0,
                    "style": discord.ButtonStyle.primary,
                    "disabled": False,
                    "label": "Update Bank",
                    # "custom_id": f"{self.id}-treaty",
                    "emoji": "💰",
                    "do_next": Button.update_bank.__name__,
                    "callback_payload": {
                        "team_id": self.id,
                    },
                },
            ]
        ]

        # Add a buttons message as a menu
        QueueTask.execute(
            {
                "task_type": TaskType.CREATE_BUTTONS,
                "payload": {
                    "team_id": self.id,
                    "guild_id": self.guild.discord_id,
                    "button_rows": button_rows,
                    "embed": {
                        "title": "Team menu",
                        "description": "Choose what you would like to do",
                        "color": 0x00FF00,
                    },
                },
            }
        )


def on_team_creation(sender, instance: Team, created, **kwargs):
    from currencies.services import CreateTrade

    if created:
        # If a guild is not set, choose the first one
        if not instance.guild:
            instance.guild = Guild.objects.first()

        wallet, _ = Wallet.objects.get_or_create(name=f"{instance.name}'s wallet")
        instance.wallet = wallet

        # TODO: Properly set guild
        guild = Guild.objects.all().first()
        instance.guild = guild

        if instance.name == "null":
            return

        # Create the role for the team
        QueueTask.execute(
            {
                "task_type": TaskType.CREATE_ROLE,
                "payload": {
                    "team_id": instance.id,
                },
            }
        )

        # Create a category for the team
        QueueTask.execute(
            {
                "task_type": TaskType.CREATE_CATEGORY,
                "payload": {
                    "team_id": instance.id,
                    "guild_id": guild.discord_id,
                },
            }
        )

        # # Create an admin channel for the team
        # admin_channel = Channel.objects.create(guild=instance.guild, name="admin")
        # instance.admin_channel = admin_channel
        # QueueTask.execute(
        #     {
        #         "task_type": TaskType.CREATE_CHANNEL,
        #         "payload": {
        #             "team_id": instance.id,
        #             "channel_bind_model_id": admin_channel.id,
        #         },
        #     }
        # )

        instance.create_team_ephemeral_channels()

        # Create a general channel for the team
        general_channel = Channel.objects.create(
            guild=instance.guild,
            name="{}-general".format(instance.name.lower().replace(" ", "-")),
        )
        instance.general_channel = general_channel
        QueueTask.execute(
            {
                "task_type": TaskType.CREATE_TEAM_CHANNEL,
                "payload": {
                    "team_id": instance.id,
                    "channel_bind_model_id": general_channel.id,
                },
            }
        )

        # Create a control channel for the team
        control_channel = Channel.objects.create(
            guild=instance.guild,
            name="{}-control".format(instance.name.lower().replace(" ", "-")),
        )
        instance.control_channel = control_channel
        QueueTask.execute(
            {
                "task_type": TaskType.CREATE_TEAM_CHANNEL,
                "payload": {
                    "team_id": instance.id,
                    "channel_bind_model_id": control_channel.id,
                },
            }
        )

        # Create voice channels for the team
        general_channel = Channel.objects.create(
            guild=instance.guild,
            name=watch_the_stars_data["teams"][instance.name]["capitol"],
        )
        instance.general_channel = general_channel
        QueueTask.execute(
            {
                "task_type": TaskType.CREATE_TEAM_VOICE_CHANNEL,
                "payload": {
                    "team_id": instance.id,
                    "name": general_channel.name,
                },
            }
        )

        # TODO: remove

        # QueueTask.execute(
        #     {
        #         "task_type": TaskType.CHANGE_TEAM,
        #         "payload": {
        #             "player_id": Member.objects.get(name="null").id,
        #             "team_id": instance.id,
        #             "guild_id": instance.guild.discord_id,
        #             "button_rows": button_rows,
        #             "embed": {
        #                 "title": "Team menu",
        #                 "description": "Choose what you would like to do",
        #                 "color": 0x00FF00,
        #             },
        #         },
        #     }
        # )

        instance.save()


post_save.connect(on_team_creation, sender=Team)
