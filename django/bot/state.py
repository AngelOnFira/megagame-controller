from asgiref.sync import async_to_sync, sync_to_async

from bot.discord_models.models import Category


async def intial_state_check(client):
    categories = [
        {
            "name": "announcements",
            "channels": [
                "world-news",  # terror tracker
                "turn-updates",  # which phase
            ],
        },
    ]

    @sync_to_async
    def get_categories():
        return list(Category.objects.all())

    categories = await get_categories()

    # Verify each team's category still exists
