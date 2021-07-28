from typing import Union

import discord
from django.db import models
from django.db.models import Count, Sum
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from bot.users.models import Member


class LoggedMessage(models.Model):

    discord_id = models.BigIntegerField(unique=True)
    server = models.BigIntegerField(_("server"))

    member = models.ForeignKey(
        "users.Member", related_name="messages_authored", on_delete=models.CASCADE
    )
    member_username = models.CharField(
        max_length=255
    )  # this can change, only the member.discord_id is a constant

    channel = models.ForeignKey("discord_channels.Channel", on_delete=models.PROTECT)

    content = models.TextField()
    num_lines = models.PositiveSmallIntegerField(default=1)
    timestamp = models.DateTimeField(auto_now_add=True)
    edited_timestamp = models.DateTimeField(null=True, blank=True)

    mentions = models.ManyToManyField(
        "users.Member", related_name="messages_mentioned_in", blank=True
    )

    class Meta:
        verbose_name = _("message")
        verbose_name_plural = _("messages")
        ordering = ["-timestamp"]

    def __str__(self):
        return str(self.discord_id)


class Download(models.Model):
    title = models.CharField(_("title"), max_length=255)
    file = models.FileField(upload_to="downloads/%Y/%m/")
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("download")
        verbose_name_plural = _("downloads")

    def __str__(self):
        return self.title
