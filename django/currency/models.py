from django.db import models
from django_fsm import FSMField, transition


class Currency(models.Model):
    name = models.CharField(max_length=20, unique=True)
    description = models.TextField(default="")


class Transaction(models.Model):
    amount = models.IntegerField(default=0)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    date = models.DateTimeField()
    wallet = models.ForeignKey('Wallet', on_delete=models.PROTECT)

    state = FSMField(default="new")

    @transition(field=state, source="new", target="created")
    def create(self):
        pass

    @transition(field=state, source="created", target="completed")
    def complete(self):
        pass


class Wallet(models.Model):
    name = models.CharField(max_length=20)


class BankAccount(models.Model):
    name = models.CharField(max_length=20)
    transactions = models.ForeignKey(Transaction, on_delete=models.PROTECT)
