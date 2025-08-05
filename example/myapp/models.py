from django.db import models


class CoffeeBean(models.Model):
    name = models.CharField(max_length=100, verbose_name="Name")
    origin = models.CharField(max_length=100, verbose_name="Origin")
    roast_level = models.CharField(max_length=50, verbose_name="Roast Level")
    flavor_notes = models.TextField(verbose_name="Flavor Notes")
    stock_quantity = models.PositiveIntegerField(
        verbose_name="Stock Quantity", default=0
    )

    def __str__(self):
        return self.name
