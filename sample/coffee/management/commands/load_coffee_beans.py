from django.core.management import BaseCommand

from sample.coffee.models import CoffeeBean

sample = [
    ("Colombian Arabica", "Colombia", "Medium", "Nutty, Fruity", 20),
    ("Ethiopian Sidamo", "Ethiopia", "Light", "Floral, Citrus", 15),
    ("Brazilian Santos", "Brazil", "Dark", "Chocolate, Spices", 25),
    ("Guatemalan Antigua", "Guatemala", "Medium", "Spicy, Full-bodied", 18),
    ("Sumatra Mandheling", "Indonesia", "Dark", "Earthy, Herbal", 30),
    ("Kenyan AA", "Kenya", "Medium-Light", "Berry, Wine", 22),
    ("Yemen Mocha", "Yemen", "Medium", "Winey, Fruity", 12),
    ("Jamaican Blue Mountain", "Jamaica", "Medium", "Mild, Smooth", 8),
    ("Vietnamese Robusta", "Vietnam", "Dark", "Strong, Harsh", 35),
    ("Peruvian Chanchamayo", "Peru", "Medium", "Citrus, Bright", 28),
    ("Costa Rican Tarrazu", "Costa Rica", "Medium", "Bright, Citrus", 26),
    ("Nicaraguan Maragogype", "Nicaragua", "Light", "Nutty, Delicate", 14),
    ("Indian Monsooned Malabar", "India", "Medium-Dark", "Spicy, Full-bodied", 19),
    ("Honduran Copan", "Honduras", "Medium", "Nutty, Chocolate", 17),
    ("Mexican Altura", "Mexico", "Medium", "Mild, Nutty", 23),
    ("Panamanian Boquete", "Panama", "Medium", "Fruity, Bright", 21),
    ("Tanzanian Peaberry", "Tanzania", "Medium", "Citrus, Bright", 15),
    ("Bolivian Caranavi", "Bolivia", "Medium", "Nutty, Chocolate", 16),
    ("Ecuadorian Loja", "Ecuador", "Medium", "Floral, Fruity", 10),
    ("Malawian AA", "Malawi", "Medium", "Bright, Citrus", 13),
]

fields = ["name", "origin", "roast_level", "flavor_notes", "stock_quantity"]


class Command(BaseCommand):
    help = "Load coffee beans into the database"

    def handle(self, *args, **options):
        for pk, bean in enumerate(sample):
            bean = dict(zip(fields, bean))
            CoffeeBean.objects.create(pk=pk, **bean)
        self.stdout.write(self.style.SUCCESS("Successfully loaded coffee beans"))
