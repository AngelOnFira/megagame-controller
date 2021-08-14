from django.db import models
from django.utils.translation import gettext_lazy as _


class TaskType(models.TextChoices):
    MESSAGE = "MG", _("Message")
    CHANGE_TEAM = "CT", _("Change Team")
    ADD_ROLE = (
        "AR",
        _("Add Role"),
    )


class Task(models.Model):
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    task_type = models.CharField(
        max_length=2, choices=TaskType.choices, default=TaskType.MESSAGE
    )

    payload = models.JSONField(default=dict)
