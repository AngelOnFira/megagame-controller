from django.db import models


class Task(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    player = models.ForeignKey(
        "player.Player", blank=True, null=True, on_delete=models.SET_NULL
    )
