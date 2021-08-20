from rest_framework import serializers

from .models import Player


class PlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        depth = 1
        fields = ("discord_member", "name", "id", "responses")
        # Get fields that are related to the model
