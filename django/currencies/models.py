from collections import defaultdict
from operator import truediv

from django_fsm import FSMField, transition

from django.db import models, transaction
from django.utils import timezone


class Currency(models.Model):
    name = models.CharField(max_length=20, unique=True)
    description = models.TextField(default="")

    emoji = models.CharField(max_length=30, blank=True, null=True)

    def __str__(self):
        return f"{self.name} (id: {self.id})"


class Trade(models.Model):
    initiating_party = models.ForeignKey(
        "teams.Team",
        on_delete=models.PROTECT,
        related_name="initiated_trades",
        null=True,
        blank=True,
    )
    receiving_party = models.ForeignKey(
        "teams.Team",
        on_delete=models.PROTECT,
        related_name="receiving_trades",
        null=True,
        blank=True,
    )

    initiating_party_accepted = models.BooleanField(default=False)
    receiving_party_accepted = models.BooleanField(default=False)

    initiating_party_discord_thread = models.ForeignKey(
        "discord_models.Channel",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="initiating_trade_thread",
    )
    receiving_party_discord_thread = models.ForeignKey(
        "discord_models.Channel",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="receiving_trade_thread",
    )

    discord_guild = models.ForeignKey(
        "discord_models.Guild", on_delete=models.PROTECT, null=True, blank=True
    )

    # Store a list of teams names that points to the their model ids. This is in
    # case someone changes a team name
    team_lookup = models.JSONField(default=dict, blank=True, null=True)

    embed_id = models.BigIntegerField(unique=True, null=True)

    state = FSMField(default="new")

    def __str__(self):
        return f"Trade between {self.initiating_party} and {self.receiving_party}"

    @transaction.atomic
    @transition(field=state, source="new", target="created")
    def create(self):
        self.created_date = timezone.now()
        self.modified_date = timezone.now()

    @transaction.atomic
    @transition(field=state, source="created", target="receiving_party_set")
    def set_receiver(self, values):
        from teams.models import Team

        self.receiving_party = Team.objects.get(id=self.team_lookup[values[0]])
        self.modified_date = timezone.now()

    @transaction.atomic
    @transition(field=state, source="new", target="completed")
    def complete(self):
        initiating_party_balance: defaultdict(
            int
        ) = self.initiating_party.get_bank_balance()

        print(initiating_party_balance)

        for transaction in Transaction.objects.filter(
            trade=self, from_wallet=self.initiating_party.wallet, state="new"
        ):
            if initiating_party_balance[transaction.currency.id] < transaction.amount:
                print(
                    f"{transaction.amount} is greater than {initiating_party_balance[transaction.currency.id]} of {transaction.currency}"
                )
                return False

        receiving_party_balance: defaultdict(
            int
        ) = self.receiving_party.get_bank_balance()

        print(receiving_party_balance)

        for transaction in Transaction.objects.filter(
            trade=self, from_wallet=self.receiving_party.wallet, state="new"
        ):
            if receiving_party_balance[transaction.currency.id] < transaction.amount:
                return False

        return True

    @transition(field=state, source="completed", target="new")
    def reset(self):
        pass


class Transaction(models.Model):
    amount = models.IntegerField(default=0, null=True, blank=True)
    currency = models.ForeignKey(
        Currency, on_delete=models.PROTECT, null=True, blank=True
    )
    trade = models.ForeignKey(
        Trade,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="transactions",
    )

    created_date = models.DateTimeField(default=timezone.now)
    modified_date = models.DateTimeField(default=timezone.now)

    from_wallet = models.ForeignKey(
        "Wallet",
        on_delete=models.PROTECT,
        default=None,
        related_name="credits",
        null=True,
        blank=True,
    )
    to_wallet = models.ForeignKey(
        "Wallet",
        on_delete=models.PROTECT,
        default=None,
        related_name="debits",
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
    @transition(field=state, source="new", target="completed")
    def complete(self):
        modified_date = timezone.now()

    def __str__(self):
        return f"{self.from_wallet} -> {self.to_wallet} ({self.amount})"


class Wallet(models.Model):
    name = models.CharField(max_length=40)

    def __str__(self):
        return f"{self.name} (id: {self.id})"


# class BankAccount(models.Model):
#     name = models.CharField(max_length=20)
#     transactions = models.ForeignKey(Transaction, on_delete=models.PROTECT)
