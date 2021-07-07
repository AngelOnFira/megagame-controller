from django.contrib import admin

from .models import Download, LoggedMessage


@admin.register(LoggedMessage)
class LoggedMessageAdmin(admin.ModelAdmin):
    list_display = ["member_username", "num_lines"]
    list_filter = ["channel", "member_username", "server"]
    ordering = ["-timestamp"]
    readonly_fields = [field.name for field in LoggedMessage._meta.get_fields()]


@admin.register(Download)
class DownloadAdmin(admin.ModelAdmin):
    list_display = ["title", "file"]
    list_filter = ["created"]
    ordering = ["-created"]
