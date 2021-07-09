from .models import Transaction
from .serializers import TransactionSerializer

from rest_framework import viewsets
from rest_framework import permissions


class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all().order_by("completed_date")
    serializer_class = TransactionSerializer
    # permission_classes = [permissions.IsAuthenticated]
