from django.db import models
from django.utils.translation import gettext_lazy as _

from asgiref.sync import sync_to_async


class Guild(models.Model):
    discord_id = models.BigIntegerField(unique=True)
