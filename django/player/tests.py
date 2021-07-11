import pytest
from currency.plugin import Plugin as CurrencyPlugin
from player.services import CreatePlayer


@pytest.mark.django_db
def test_create_player():
    CreatePlayer.execute({})

# @pytest.mark.django_db
# def test_send_transaction_message():
#     currency_plugin = CurrencyPlugin()
#     currency_plugin.on_message("!control send "