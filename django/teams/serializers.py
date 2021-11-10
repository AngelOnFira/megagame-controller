from players.models import Player
from rest_framework import serializers

from .models import Team


class TeamPlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        fields = ["id"]


class TeamSerializer(serializers.ModelSerializer):

    players = TeamPlayerSerializer(many=True, read_only=True)

    class Meta:
        model = Team
        fields = ["name", "description", "emoji", "wallet", "players", "id"]
