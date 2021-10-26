from bot.discord_models.models import Guild
from currencies.models import Wallet
from django.db import models
from django.db.models.signals import post_save
from responses.models import Response
from teams.models import Team


class Player(models.Model):
    wallet = models.OneToOneField(Wallet, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, default="")

    team = models.ForeignKey(
        "teams.Team",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="players",
    )

    responses = models.ManyToManyField(Response)

    guild = models.ForeignKey(
        "discord_models.Guild", on_delete=models.CASCADE, null=True
    )

    def __str__(self):
        return f"{self.name}/{self.discord_member.name}"


def default_team(sender, instance, created, **kwargs):
    # Have to import here to prevent circular imports
    from players.services import CreatePlayer

    if created:
        team, _ = Team.objects.get_or_create(name="null")
        instance.team = team

        # TODO: Properly set guild
        guild = Guild.objects.all().first()

        if not guild:
            guild = Guild.objects.create(discord_id=0)

        instance.guild = guild

        team.guild = guild
        team.save()

        instance.save()


post_save.connect(default_team, sender=Player)
