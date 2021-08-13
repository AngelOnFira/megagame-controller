from .models import Transaction, Wallet
from .serializers import TransactionSerializer, WalletSerializer

from rest_framework import viewsets
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from collections import defaultdict


class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all().order_by("modified_date")
    serializer_class = TransactionSerializer
    # permission_classes = [permissions.IsAuthenticated]


class WalletViewSet(viewsets.ModelViewSet):
    queryset = Wallet.objects.all()
    serializer_class = WalletSerializer
    # permission_classes = [permissions.IsAuthenticated]

    @action(
        methods=["get"],
        url_path="wallets",
        url_name="wallets",
        detail=False,
        permission_classes=[permissions.AllowAny],
    )
    def wallets(self, request):
        wallets = Wallet.objects.all()

        wallets_aggrigated = []
        for wallet in wallets:
            wallet_balance = {"amounts": defaultdict(int)}

            wallet_balance["id"] = wallet.id

            for credit in wallet.credits.filter(state="completed"):
                print(credit)
                wallet_balance["amounts"][credit.currency.name] -= credit.amount

            for debit in wallet.debits.filter(state="completed"):
                wallet_balance["amounts"][debit.currency.name] += debit.amount

            wallets_aggrigated.append(wallet_balance)

        # print the body
        return Response(wallets_aggrigated)
