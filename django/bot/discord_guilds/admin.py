from django.contrib import admin

from .models import Guild


@admin.register(Guild)
class GuildAdmin(admin.ModelAdmin):
    pass
    # list_display = ("name", "allow_nsfw")
    # list_filter = ("allow_nsfw",)
    # search_fields = ("name",)
