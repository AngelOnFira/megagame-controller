import pytest

from .services import CreateCurrency, CreateWallet


@pytest.mark.django_db
def test_create_currency():
    CreateCurrency.execute({"name": "Cre dit", "description": "Credit currency"})


# @pytest.mark.django_db
# def test_create_transaction():
#     wallet = CreateWallet.execute({"name": "Wallet", "description": "Wallet"})
#     CreateCurrency.execute({"name": "Credit", "description": "Credit currency"})
#     CreateTransaction.execute(
#         {"currency_name": "Credit", "amount": 100, "destination_wallet": wallet.id}
#     )
