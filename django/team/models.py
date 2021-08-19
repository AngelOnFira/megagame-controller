from django.db import models
from django.db.models.signals import post_save


from currency.models import Wallet
from bot.discord_roles.models import Role
from tasks.services import QueueTask
from tasks.models import TaskType
from bot.discord_guilds.models import Guild
import emojis

# Create your models here.
class Team(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    guild = models.ForeignKey(
        "discord_guilds.Guild", on_delete=models.CASCADE, null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    emoji = models.CharField(max_length=30, blank=True, null=True)

    wallet = models.ForeignKey(
        "currency.Wallet", on_delete=models.CASCADE, null=True, blank=True
    )

    role = models.OneToOneField(
        "discord_roles.Role", on_delete=models.CASCADE, null=True, blank=True
    )

    category = models.OneToOneField(
        "discord_roles.Category", on_delete=models.CASCADE, null=True, blank=True
    )

    def __str__(self):
        if self.emoji:
            return f"{self.name} {emojis.decode(self.emoji)} ({self.id})"

        return f"{self.name} ({self.id})"


def default_wallet(sender, instance, created, **kwargs):

    if created:
        # If a guild is not set, choose the first one
        if not instance.guild:
            instance.guild = Guild.objects.first()


        wallet, _ = Wallet.objects.get_or_create(name=f"{instance.name}'s wallet")
        instance.wallet = wallet

        # TODO: Properly set guild
        guild = Guild.objects.all().first()
        instance.guild = guild

        instance.save()

        # # Create the role for the team
        # QueueTask.execute(
        #     {
        #         "task_type": TaskType.CREATE_ROLE,
        #         "payload": {
        #             "team_id": instance.id,
        #         },
        #     }
        # )

        # # Create a category for the team
        # QueueTask.execute(
        #     {
        #         "task_type": TaskType.CREATE_CATEGORY,
        #         "payload": {
        #             "team_id": instance.id,
        #         },
        #     }
        # )

        # # Create a channel for the team
        # QueueTask.execute(
        #     {
        #         "task_type": TaskType.CREATE_CHANNEL,
        #         "payload": {
        #             "team_id": instance.id,
        #             "channel_name": "general",
        #         },
        #     }
        # )


post_save.connect(default_wallet, sender=Team)
