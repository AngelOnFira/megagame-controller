from django.db import models

# Create your models here.
class Team(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    emoji = models.CharField(max_length=30, blank=True)

    wallet = models.ForeignKey(
        "currency.Wallet", on_delete=models.CASCADE, null=True, blank=True
    )
