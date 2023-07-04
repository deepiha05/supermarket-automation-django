from django.contrib import admin

# Register your models here.
from superMarket.models import product, transaction, sold_product

admin.site.register(product)
admin.site.register(transaction)
admin.site.register(sold_product)