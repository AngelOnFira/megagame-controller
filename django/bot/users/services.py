from django import forms
from service_objects.services import Service

from .models import Member


class CreateMember(Service):
    discord_id = forms.CharField()
    discord_name = forms.CharField()

    def process(self):
        discord_id = self.cleaned_data.get("discord_id")
        discord_name = self.cleaned_data.get("discord_name")

        a = Member.objects.get_or_create(
            discord_id=discord_id, defaults={"name": discord_name}
        )
        member, created = a
        if member.name != discord_name:
            member.name = discord_name
            member.save()
        return member, created
