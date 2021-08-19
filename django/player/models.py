from django.db import models
from currency.models import Wallet
from django.db.models.signals import post_save
from team.models import Team
from responses.models import Response
from bot.discord_guilds.models import Guild


class Player(models.Model):
    wallet = models.OneToOneField(Wallet, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, default="")

    team = models.ForeignKey(
        "team.Team",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="players",
    )

    responses = models.ManyToManyField(Response)

    guild = models.ForeignKey(
        "discord_guilds.Guild", on_delete=models.CASCADE, null=True
    )


def default_team(sender, instance, created, **kwargs):
    # Have to import here to prevent circular imports
    from player.services import CreatePlayer

    if created:
        team, _ = Team.objects.get_or_create(name="null")
        instance.team = team

        # TODO: Properly set guild
        guild = Guild.objects.all().first()
        instance.guild = guild

        team.guild = guild
        team.save()
        
        instance.save()


post_save.connect(default_team, sender=Player)
