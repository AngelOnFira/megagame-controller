from .models import Player
from rest_framework import serializers


class PlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        depth = 1
        fields = ("discord_member","name","id")
        # Get fields that are related to the model
