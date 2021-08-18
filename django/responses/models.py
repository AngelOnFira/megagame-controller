from django.db import models


class Response(models.Model):
    question_id = models.IntegerField(default=0)
    response = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
