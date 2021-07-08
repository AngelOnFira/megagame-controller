from django.db import models
from currency.models import Wallet
from django.db.models.signals import post_save


class Player(models.Model):
    wallet = models.OneToOneField(Wallet, on_delete=models.CASCADE)
