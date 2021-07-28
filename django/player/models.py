from django.db import models
from currency.models import Wallet
from django.db.models.signals import post_save
from team.models import Team


class Player(models.Model):
    wallet = models.OneToOneField(Wallet, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, default="")

    team = models.ForeignKey(
        "team.Team", on_delete=models.CASCADE, null=True, blank=True
    )

def default_team(sender, instance, created, **kwargs):
    # Have to import here to prevent circular imports
    from player.services import CreatePlayer

    if created:
        team, _ = Team.objects.get_or_create(name="temp team")
        instance.team = team
        instance.save()


post_save.connect(default_team, sender=Player)
