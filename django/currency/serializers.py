from .models import Transaction
from rest_framework import serializers


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = "__all__"  # ['url', 'username', 'email', 'groups']
