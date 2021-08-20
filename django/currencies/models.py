from django_fsm import FSMField, transition

from django.db import models, transaction
from django.utils import timezone


class Currency(models.Model):
    name = models.CharField(max_length=20, unique=True)
    description = models.TextField(default="")

    emoji = models.CharField(max_length=1, blank=True, null=True)

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

    discord_channel = models.ForeignKey(
        "discord_models.Channel", on_delete=models.PROTECT, null=True, blank=True
    )
    discord_guild = models.ForeignKey(
        "discord_models.Guild", on_delete=models.PROTECT, null=True, blank=True
    )

    team_lookup = models.JSONField(default=dict, blank=True, null=True)
    currency_lookup = models.JSONField(default=dict, blank=True, null=True)

    state = FSMField(default="new")

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


class Transaction(models.Model):
    # current_message_id = models.IntegerField(default=0, unique=True)

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

    emoji_lookup = models.JSONField(default=None, null=True, blank=True)

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
    name = models.CharField(max_length=40)


# class BankAccount(models.Model):
#     name = models.CharField(max_length=20)
#     transactions = models.ForeignKey(Transaction, on_delete=models.PROTECT)
