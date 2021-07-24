from .models import Player
from .serializers import PlayerSerializer

from rest_framework import viewsets
from rest_framework import permissions

from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from rest_framework.decorators import action

from tasks.services import QueueMessage


class PlayerViewSet(viewsets.ModelViewSet):
    queryset = Player.objects.all().order_by("name")
    serializer_class = PlayerSerializer

    @action(
        methods=["post"],
        url_path="send-message",
        url_name="send_message",
        detail=False,
        permission_classes=[permissions.AllowAny],
    )
    def send_message(self, request):
        QueueMessage.execute(
            {"player_id": request.data["playerId"], "message": request.data["message"]}
        )
        # print the body
        print(request.data)
        return Response(status=HTTP_200_OK)
