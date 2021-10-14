from django.db import models
from django.utils.translation import gettext_lazy as _


class TaskType(models.TextChoices):
    MESSAGE = "MSG", _("Message")
    CHANGE_TEAM = "CHT", _("Change Team")
    CREATE_ROLE = (
        "CRO",
        _("Create Role"),
    )
    CREATE_CATEGORY = (
        "CCA",
        _("Create Category"),
    )
    CREATE_CHANNEL = (
        "CCH",
        _("Create Channel"),
    )
    CREATE_DROPDOWN = (
        "CDR",
        _("Create Dropdown"),
    )
    CREATE_BUTTONS = (
        "CBT",
        _("Create Buttons"),
    )
    TRADE_SELECT_RECEIVER = (
        "TSR",
        _("Create Transaction"),
    )
    CREATE_MESSAGE = (
        "CMS",
        _("Create Message"),
    )
    CREATE_THREAD = (
        "CTH",
        _("Create Thread"),
    )


class Task(models.Model):
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    task_type = models.CharField(
        max_length=3, choices=TaskType.choices, default=TaskType.MESSAGE
    )

    payload = models.JSONField(default=dict)
