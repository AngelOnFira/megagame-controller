from rest_framework import serializers

from .models import LoggedMessage


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoggedMessage
        fields = "__all__"  # ['url', 'username', 'email', 'groups']
