from django.db import models


class CoffeeBean(models.Model):
    name = models.CharField(max_length=100)
    origin = models.CharField(max_length=100)
    roast_level = models.CharField(max_length=50)
    flavor_notes = models.TextField()
    stock_quantity = models.IntegerField()

    def __str__(self):
        return self.name
