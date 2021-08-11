from .models import Team
from rest_framework import serializers
from player.models import Player

class TeamPlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        fields = ['id']

class TeamSerializer(serializers.ModelSerializer):

    players = TeamPlayerSerializer(many=True)
    class Meta:
        model = Team
        fields = ["name", "description", "emoji", "wallet", "players"]
