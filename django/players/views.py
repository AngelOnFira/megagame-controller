from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from tasks.models import TaskType
from tasks.services import QueueTask
from teams.models import Team

from .models import Player
from .serializers import PlayerSerializer


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
        QueueTask.execute(
            {
                "task_type": TaskType.MESSAGE,
                "payload": {
                    "player_id": request.data["playerId"],
                    "message": request.data["message"],
                },
            }
        )
        # print the body
        print(request.data)
        return Response(status=HTTP_200_OK)

    @action(
        methods=["post"],
        url_path="change-team",
        url_name="change_team",
        detail=False,
        permission_classes=[permissions.AllowAny],
    )
    def change_team(self, request):
        player = Player.objects.get(id=request.data["playerId"])
        team = Team.objects.get(id=request.data["teamId"])

        QueueTask.execute(
            {
                "task_type": TaskType.CHANGE_TEAM,
                "payload": {
                    "player_id": request.data["playerId"],
                    "new_team_id": request.data["teamId"],
                },
            }
        )
        # print the body
        print(request.data)
        return Response(status=HTTP_200_OK)
