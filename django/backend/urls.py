from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

from rest_framework import routers
from bot.plugins.stats import views as stats_views
from currency import views as currency_views
from team import views as team_views
from player import views as player_views

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

router = routers.DefaultRouter()
router.register(r"stats", stats_views.MessageViewSet)
router.register(r"transactions", currency_views.TransactionViewSet)
router.register(r"wallets", currency_views.WalletViewSet)
router.register(r"teams", team_views.TeamViewSet)
router.register(r"players", player_views.PlayerViewSet)

schema_view = get_schema_view(
    # openapi.Info(
    #     title="Snippets API",
    #     default_version="v1",
    #     description="Test description",
    #     terms_of_service="https://www.google.com/policies/terms/",
    #     contact=openapi.Contact(email="contact@snippets.local"),
    #     license=openapi.License(name="BSD License"),
    # ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # admin
    path("admin/", admin.site.urls),
    # third party urls
    path(r"", include(router.urls)),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    path(
        r"swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path(r"redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
]
