from django.db import models
from django.db.models.signals import post_save


from currency.models import Wallet

# Create your models here.
class Team(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    emoji = models.CharField(max_length=30, blank=True)

    wallet = models.ForeignKey(
        "currency.Wallet", on_delete=models.CASCADE, null=True, blank=True
    )


def default_wallet(sender, instance, created, **kwargs):

    if created:
        wallet, _ = Wallet.objects.get_or_create(name=f"{instance.name}'s wallet")
        instance.wallet = wallet
        instance.save()


post_save.connect(default_wallet, sender=Team)
