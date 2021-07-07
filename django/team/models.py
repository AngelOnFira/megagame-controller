from django.db import models
from bot.users import models as user_models

# Create your models here.
class Team(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    players = models.ManyToManyField('users.Member', related_name='teams')