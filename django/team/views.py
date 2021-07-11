from .models import Team
from .serializers import TeamSerializer

from rest_framework import viewsets
from rest_framework import permissions

from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED


class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.all().order_by("name")
    serializer_class = TeamSerializer
    # permission_classes = [permissions.IsAuthenticated]

    # def create(self, request):
    #     serializer = self.get_serializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #     self.perform_create(serializer)
    #     headers = self.get_success_headers(serializer.data)
    #     return Response(serializer.data, status=HTTP_201_CREATED, headers=headers)
