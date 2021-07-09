from bot.plugins.events import receiver
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save

from player.models import Player


from asgiref.sync import sync_to_async


class MemberQuerySet(models.QuerySet):
    async def _get_member(self, discord_user):
        a = await sync_to_async(self.get_or_create)(
            discord_id=discord_user.id, defaults={"name": discord_user.name}
        )
        member, created = a
        if member.name != discord_user.name:
            member.name = discord_user.name
            sync_to_async(member.save())
        return member, created

    async def from_message(self, message):
        a = await self._get_member(message.author)
        return a[0]

    async def from_mentions(self, mentions):
        return [self._get_member(member)[0] for member in mentions]

    async def from_discord(self, discord_user):
        return self._get_member(discord_user)[0]


class Member(models.Model):
    discord_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(_("name"), max_length=255)
    last_seen = models.DateTimeField(null=True, blank=True)

    is_bot = models.BooleanField(default=False)
    can_admin_bot = models.BooleanField(default=False)

    objects = MemberQuerySet.as_manager()

    player = models.OneToOneField(
        Player, null=True, blank=True, on_delete=models.CASCADE
    )

    def __str__(self):
        return "<@{} name={}>".format(self.discord_id, self.name)


def create_player(sender, instance, created, **kwargs):
    # Have to import here to prevent circular imports
    from player.services import CreatePlayer

    if created:
        player = CreatePlayer.execute({})
        instance.player = player
        instance.save()


post_save.connect(create_player, sender=Member)
