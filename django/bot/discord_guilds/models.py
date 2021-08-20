from asgiref.sync import sync_to_async

from django.db import models
from django.utils.translation import gettext_lazy as _


class Guild(models.Model):
    discord_id = models.BigIntegerField(unique=True)
