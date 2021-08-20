import pytest
from currencies.plugin import Plugin as CurrencyPlugin
from players.services import CreatePlayer


@pytest.mark.django_db
def test_create_player():
    CreatePlayer.execute({})


# @pytest.mark.django_db
# def test_send_transaction_message():
#     currency_plugin = CurrencyPlugin()
#     currency_plugin.on_message("!control send "
