from django.db import models
from django.db.models.signals import post_save


from currency.models import Wallet
from bot.discord_roles.models import Role
from tasks.services import QueueTask
from tasks.models import TaskType
from bot.discord_guilds.models import Guild

# Create your models here.
class Team(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    guild = models.ForeignKey(
        "discord_guilds.Guild", on_delete=models.CASCADE, null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    emoji = models.CharField(max_length=30, blank=True)
    wallet = models.ForeignKey(
        "currency.Wallet", on_delete=models.CASCADE, null=True, blank=True
    )

    role = models.OneToOneField(
        "discord_roles.Role", on_delete=models.CASCADE, null=True, blank=True
    )


def default_wallet(sender, instance, created, **kwargs):

    if created:
        wallet, _ = Wallet.objects.get_or_create(name=f"{instance.name}'s wallet")
        instance.wallet = wallet

        # TODO: Properly set guild
        guild = Guild.objects.all().first()
        instance.guild = guild

        instance.save()

        # Create the role for the team
        QueueTask.execute(
            {
                "task_type": TaskType.ADD_ROLE,
                "payload": {
                    "team_id": instance.id,
                },
            }
        )


post_save.connect(default_wallet, sender=Team)
