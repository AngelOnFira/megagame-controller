from django.contrib import admin

from .models import Category, Channel, Guild, Role


@admin.register(Guild)
class GuildAdmin(admin.ModelAdmin):
    pass


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ("name", "allow_nsfw")
    list_filter = ("allow_nsfw",)
    search_fields = ("name",)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    pass


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    pass
