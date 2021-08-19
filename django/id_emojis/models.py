from django.db import models

class IDEmoji(models.Model):
    """
    An emoji to be used in a user's profile.
    """
    emoji = models.CharField(max_length=1)
    emoji_text = models.CharField(max_length=30)

    def __str__(self):
        return self.emoji_text