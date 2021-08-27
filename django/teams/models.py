import json

import discord
import emojis
from asgiref.sync import sync_to_async

from bot.discord_models.models import Channel, Guild, Role
from currencies.models import Wallet
from django.db import models
from django.db.models.signals import post_save
from tasks.models import TaskType
from tasks.services import QueueTask


# Create your models here.
class Team(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    guild = models.ForeignKey(
        "discord_models.Guild", on_delete=models.CASCADE, null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    emoji = models.CharField(max_length=30, blank=True, null=True)

    wallet = models.ForeignKey(
        "currencies.Wallet", on_delete=models.CASCADE, null=True, blank=True
    )

    role = models.OneToOneField(
        "discord_models.Role", on_delete=models.CASCADE, null=True, blank=True
    )

    category = models.OneToOneField(
        "discord_models.Category", on_delete=models.CASCADE, null=True, blank=True
    )

    general_channel = models.OneToOneField(
        "discord_models.Channel",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="team_general_channel",
    )

    menu_channel = models.OneToOneField(
        "discord_models.Channel",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="team_menu_channel",
    )

    bank_embed = models.BigIntegerField(null=True, blank=True, default=0)

    def __str__(self):
        if self.emoji:
            return f"{self.name} {emojis.decode(self.emoji)} ({self.id})"

        return f"{self.name} ({self.id})"


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

        # Create a menu channel for the team
        menu_channel = Channel.objects.create(guild=instance.guild, name="menu")
        instance.menu_channel = menu_channel
        QueueTask.execute(
            {
                "task_type": TaskType.CREATE_CHANNEL,
                "payload": {
                    "team_id": instance.id,
                    "channel_bind_model_id": menu_channel.id,
                },
            }
        )

        # Create a general channel for the team
        general_channel = Channel.objects.create(guild=instance.guild, name="general")
        instance.general_channel = general_channel
        QueueTask.execute(
            {
                "task_type": TaskType.CREATE_CHANNEL,
                "payload": {
                    "team_id": instance.id,
                    "channel_bind_model_id": general_channel.id,
                },
            }
        )

        # Add bank message
        QueueTask.execute(
            {
                "task_type": TaskType.CREATE_MESSAGE,
                "payload": {
                    "channel_id": instance.menu_channel.id,
                    "message": "team_bank_embed",
                    "team_id": instance.id,
                },
            }
        )

        button_rows = [
            [
                {
                    "x": 0,
                    "y": 0,
                    "style": discord.ButtonStyle.primary,
                    "disabled": False,
                    "label": "Start trade",
                    "custom_id": f"{instance.id}",
                    "emoji": "💱",
                    "do_next": "start_trading",
                    "callback_payload": {},
                }
            ]
        ]

        # Add a buttons message as a menu
        QueueTask.execute(
            {
                "task_type": TaskType.CREATE_BUTTONS,
                "payload": {
                    "team_id": instance.id,
                    "guild_id": instance.guild.discord_id,
                    "button_rows": button_rows,
                    "embed": {
                        "title": "Team menu",
                        "description": "Choose what you would like to do",
                        "color": 0x00FF00,
                    },
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
