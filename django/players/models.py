from bot.discord_models.models import Guild
from django.db import models
from django.db.models.signals import post_save
from responses.models import Response


class Player(models.Model):
    name = models.CharField(max_length=100, default="", blank=True, null=True)

    team = models.ForeignKey(
        "teams.Team",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="players",
    )

    responses = models.ManyToManyField(Response, blank=True)

    guild = models.ForeignKey(
        "discord_models.Guild", on_delete=models.CASCADE, null=True
    )

    def __str__(self):
        return f"{self.name}/{self.discord_member.name} ({self.team.name})"


def default_team(sender, instance, created, **kwargs):
    # Have to import here to prevent circular imports
    from players.services import CreatePlayer
    from teams.models import Team

    if created:
        # TODO: set back to null
        team, _ = Team.objects.get_or_create(name="null")
        # team, _ = Team.objects.get_or_create(name="United Kingdom")
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
