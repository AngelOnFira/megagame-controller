from django.db import models
from django.utils import timezone
from django_fsm import FSMField, transition
from django.db import transaction


class Currency(models.Model):
    name = models.CharField(max_length=20, unique=True)
    description = models.TextField(default="")


class Transaction(models.Model):
    current_message_id = models.IntegerField(default=0, unique=True)

    amount = models.IntegerField(default=0, null=True, blank=True)
    currency = models.ForeignKey(
        Currency, on_delete=models.PROTECT, null=True, blank=True
    )

    created_date = models.DateTimeField(default=timezone.now)
    modified_date = models.DateTimeField(default=timezone.now)

    from_wallet = models.ForeignKey(
        "Wallet",
        on_delete=models.PROTECT,
        default=None,
        related_name="from_wallet",
        null=True,
        blank=True,
    )
    to_wallet = models.ForeignKey(
        "Wallet",
        on_delete=models.PROTECT,
        default=None,
        related_name="to_wallet",
        null=True,
        blank=True,
    )

    state = FSMField(default="new")

    @transaction.atomic
    @transition(field=state, source="new", target="created")
    def create(self):
        created_date = timezone.now()
        modified_date = timezone.now()

    @transaction.atomic
    @transition(field=state, source="created", target="destination_set")
    def set_destination(self):
        modified_date = timezone.now()

    @transaction.atomic
    @transition(field=state, source="destination_set", target="currency_set")
    def set_currency(self):
        modified_date = timezone.now()

    @transaction.atomic
    @transition(field=state, source="currency_set", target="amount_set")
    def set_amount(self):
        modified_date = timezone.now()

    @transaction.atomic
    @transition(field=state, source="created", target="completed")
    def complete(self):
        modified_date = timezone.now()


class Wallet(models.Model):
    name = models.CharField(max_length=20)


# class BankAccount(models.Model):
#     name = models.CharField(max_length=20)
#     transactions = models.ForeignKey(Transaction, on_delete=models.PROTECT)
