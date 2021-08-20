from asgiref.sync import sync_to_async

from django.db import models
from django.utils.translation import gettext_lazy as _

# class RoleQuerySet(models.QuerySet):
#     async def from_message(self, message):
#         discord_id = message.channel.id
#         channel, created = await sync_to_async(self.get_or_create)(
#             discord_id=discord_id, defaults={"name": message.channel.name}
#         )
#         return channel


class Role(models.Model):
    discord_id = models.BigIntegerField(unique=True)


class Category(models.Model):
    discord_id = models.BigIntegerField(unique=True)
