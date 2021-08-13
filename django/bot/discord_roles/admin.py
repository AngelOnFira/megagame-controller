from django.contrib import admin

from .models import Role


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    pass
    # list_display = ("name", "allow_nsfw")
    # list_filter = ("allow_nsfw",)
    # search_fields = ("name",)
