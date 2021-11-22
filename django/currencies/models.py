from collections import defaultdict
from locale import currency
from operator import truediv

from django_fsm import FSMField, transition

from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from players.models import Player


class CurrencyType(models.TextChoices):
    ADMIN = "ADM", _("Admin")
    COMMON = "COM", _("Common")
    RARE = "RAR", _("Rare")
    LOGISTICS = "LOG", _("Logistics")
    HIDDEN = "HID", _("Hidden")
    SPECIAL = "SPE", _("Special")


class Currency(models.Model):
    name = models.CharField(max_length=20, unique=True)
    description = models.TextField(default="")

    currency_type = models.CharField(
        max_length=3, choices=CurrencyType.choices, default=CurrencyType.HIDDEN
    )

    emoji = models.CharField(max_length=30, blank=True, null=True)

    def __str__(self):
        return f"{self.name} (id: {self.id})"


class Transaction(models.Model):
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

    initiating_player = models.ForeignKey(
        Player,
        on_delete=models.PROTECT,
        default=None,
        related_name="transaction",
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

    transactions = models.ManyToManyField(Transaction)

    first_iteration = models.BooleanField(default=True)
    initiating_party_accepted = models.BooleanField(default=False)
    receiving_party_accepted = models.BooleanField(default=False)

    locked_in = models.BooleanField(default=False)

    initiating_party_discord_trade_thread = models.ForeignKey(
        "discord_models.Channel",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="initiating_discord_trade_thread",
    )

    receiving_party_discord_trade_thread = models.ForeignKey(
        "discord_models.Channel",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="receiving_discord_trade_thread",
    )

    discord_guild = models.ForeignKey(
        "discord_models.Guild", on_delete=models.PROTECT, null=True, blank=True
    )

    # Store a list of teams names that points to the their model ids. This is in
    # case someone changes a team name
    team_lookup = models.JSONField(default=dict, blank=True, null=True)

    initiating_embed_id = models.BigIntegerField(unique=True, null=True)
    receiving_embed_id = models.BigIntegerField(unique=True, null=True)

    state = FSMField(default="initiating_party_view")

    def __str__(self):
        return f"Trade between {self.initiating_party} and {self.receiving_party}"

    # States
    #
    # new
    # initiating_party_accepted
    # receiving_party_accepted
    # initiating_party_confirmed
    # completed

    @transaction.atomic
    @transition(field=state, source="new", target="initiating_party_accepted")
    def initiating_party_accept(self):
        self.created_date = timezone.now()
        self.modified_date = timezone.now()

    @transaction.atomic
    @transition(
        field=state, source="receiving_party_view", target="initiating_party_view"
    )
    def pass_to_initiating(self):
        if self.first_iteration:
            self.first_iteration = False
            return
        self.receiving_party_accepted = True

    @transaction.atomic
    @transition(
        field=state, source="initiating_party_view", target="receiving_party_view"
    )
    def pass_to_receiving(self):
        if self.first_iteration:
            self.first_iteration = False
            return
        self.initiating_party_accepted = True

    def swap_views(self):
        if self.state == "initiating_party_view":
            self.pass_to_receiving()
        else:
            self.pass_to_initiating()

    @transaction.atomic
    @transition(
        field=state,
        source=["receiving_party_view", "initiating_party_view"],
        target="completed",
    )
    def complete(self):
        initiating_party_balance = self.initiating_party.wallet.get_bank_balance()

        for transaction in Transaction.objects.filter(
            trade=self, from_wallet=self.initiating_party.wallet, state="new"
        ):
            if initiating_party_balance[transaction.currency] < transaction.amount:
                print(
                    f"{transaction.amount} is greater than {initiating_party_balance[transaction.currency.id]} of {transaction.currency}"
                )
                return False

        receiving_party_balance: defaultdict(
            int
        ) = self.receiving_party.wallet.get_bank_balance()

        for transaction in Transaction.objects.filter(
            trade=self, from_wallet=self.receiving_party.wallet, state="new"
        ):
            if receiving_party_balance[transaction.currency.id] < transaction.amount:
                return False

        for transaction in Transaction.objects.filter(trade=self):
            transaction.complete()
            transaction.save()

        # TODO: Add recipt

        return True

    @transition(field=state, source="completed", target="new")
    def reset(self):
        pass


class Wallet(models.Model):
    name = models.CharField(max_length=40)

    def __str__(self):
        return f"{self.name} (id: {self.id})"

    def get_currencies_available(self) -> list[Currency]:
        """Get all currencies in this wallet that are greater than 0

        Returns:
            list[Currency]: List of currencies
        """
        return list(
            currency for currency, count in self.get_bank_balance().items() if count > 0
        )

    def get_bank_balance(self, new=False) -> dict[Currency, int]:
        """Get the bank balance of this wallet

        Returns:
            dict[Currency, int]: Dictionary of currencies and their count
        """
        transaction_totals = defaultdict(int)

        for debit in self.debits.filter(state="completed"):
            transaction_totals[debit.currency] += debit.amount

        to_check = ["completed"]
        if new:
            to_check.append("new")

        for credit in self.credits.filter(state__in=to_check):
            transaction_totals[credit.currency] -= credit.amount

        return dict(transaction_totals)


# class BankAccount(models.Model):
#     name = models.CharField(max_length=20)
#     transactions = models.ForeignKey(Transaction, on_delete=models.PROTECT)


class Payment(models.Model):
    action = models.TextField(default="")
    cost = models.IntegerField(default=0)
    completion_amount = models.IntegerField(default=0)

    embed_id = models.BigIntegerField(null=True, blank=True)
    channel_id = models.BigIntegerField(null=True, blank=True)
    transactions = models.ManyToManyField(Transaction)

    completed = models.BooleanField(default=False)
