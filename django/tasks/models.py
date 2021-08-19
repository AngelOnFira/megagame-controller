from django.db import models
from django.utils.translation import gettext_lazy as _


class TaskType(models.TextChoices):
    MESSAGE = "MG", _("Message")
    CHANGE_TEAM = "CT", _("Change Team")
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
    CREATE_TRANSACTION = (
        "CTR",
        _("Create Transaction"),
    )


class Task(models.Model):
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    task_type = models.CharField(
        max_length=3, choices=TaskType.choices, default=TaskType.MESSAGE
    )

    payload = models.JSONField(default=dict)
