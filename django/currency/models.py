from django.db import models
from django.utils import timezone
from django_fsm import FSMField, transition
from django.db import transaction


class Currency(models.Model):
    name = models.CharField(max_length=20, unique=True)
    description = models.TextField(default="")


class Transaction(models.Model):
    amount = models.IntegerField(default=0)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)

    created_date = models.DateTimeField(default=timezone.now)
    completed_date = models.DateTimeField(default=timezone.now)

    from_wallet = models.ForeignKey(
        "Wallet", on_delete=models.PROTECT, default=None, related_name="from_wallet"
    )
    to_wallet = models.ForeignKey(
        "Wallet", on_delete=models.PROTECT, default=None, related_name="to_wallet"
    )

    state = FSMField(default="new")

    @transaction.atomic
    @transition(field=state, source="new", target="created")
    def create(self):
        created_date = timezone.now()
        completed_date = timezone.now()

    @transaction.atomic
    @transition(field=state, source="created", target="completed")
    def complete(self):
        completed_date = timezone.now()


class Wallet(models.Model):
    name = models.CharField(max_length=20)


class BankAccount(models.Model):
    name = models.CharField(max_length=20)
    transactions = models.ForeignKey(Transaction, on_delete=models.PROTECT)
