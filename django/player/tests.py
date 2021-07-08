import pytest
from player.services import CreatePlayer


@pytest.mark.django_db
def test_create_player():
    CreatePlayer.execute({})
