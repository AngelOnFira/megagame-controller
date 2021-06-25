from .models import LoggedMessage
from .serializers import MessageSerializer

from rest_framework import viewsets
from rest_framework import permissions


class MessageViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """

    queryset = LoggedMessage.objects.all().order_by("timestamp")
    serializer_class = MessageSerializer
    # permission_classes = [permissions.IsAuthenticated]
