from django.db import models

# Create your models here.
class Currency(models.Model):
    name = models.CharField(max_length=20)
    symbol = models.CharField(max_length=3)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    def __str__(self):
        return self.name

# Transaction class
class Transaction(models.Model):
    amount = models.IntegerField(default=0)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    date = models.DateTimeField()
    def __str__(self):
        return self.amount

# Wallet class that is a collection of transactions
class Wallet(models.Model):
    name = models.CharField(max_length=20)
    transactions = models.ForeignKey(Transaction, on_delete=models.PROTECT)