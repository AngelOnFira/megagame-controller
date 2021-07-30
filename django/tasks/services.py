from django import forms
from service_objects.services import Service
from .models import Task
from player.models import Player


class QueueMessage(Service):
    player_id = forms.IntegerField()
    message = forms.CharField()
    def process(self):
        player_id = self.cleaned_data['player_id']
        message = self.cleaned_data['message']

        player = Player.objects.get(id=player_id)

        task = Task.objects.create(player=player, description=message)

        print("created")