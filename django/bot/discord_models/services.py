from service_objects.services import Service

from django import forms

from .models import Guild


class CreateGuild(Service):
    discord_id = forms.CharField()

    def process(self):
        discord_id = self.cleaned_data.get("discord_id")

        guild, created = Guild.objects.get_or_create(discord_id=discord_id)
        return guild, created
