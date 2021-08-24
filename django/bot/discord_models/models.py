from asgiref.sync import sync_to_async

from django.db import models
from django.utils.translation import gettext_lazy as _


class Guild(models.Model):
    discord_id = models.BigIntegerField(unique=True)


class ChannelQuerySet(models.QuerySet):
    async def from_message(self, message):
        discord_id = message.channel.id
        channel, created = await sync_to_async(self.get_or_create)(
            discord_id=discord_id, defaults={"name": message.channel.name}
        )
        return channel


class Channel(models.Model):
    discord_id = models.BigIntegerField(unique=True)
    name = models.CharField(_("name"), max_length=50)

    allow_nsfw = models.BooleanField(default=False)

    objects = ChannelQuerySet.as_manager()

    def __str__(self):
        return self.name


class Role(models.Model):
    discord_id = models.BigIntegerField(unique=True)
    name = models.CharField(_("name"), max_length=50, default="")


class Category(models.Model):
    discord_id = models.BigIntegerField(unique=True)
