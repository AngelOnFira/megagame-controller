from .models import LoggedMessage
from rest_framework import serializers


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoggedMessage
        fields = '__all__' #['url', 'username', 'email', 'groups']