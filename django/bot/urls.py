from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView
from rest_framework import routers
from bot.stats import stats_views

router = routers.DefaultRouter()
router.register(r'stats', stats_views.MessageViewSet)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", TemplateView.as_view(template_name="base.html")),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
]
