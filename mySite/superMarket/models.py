from pyexpat import model
from django.db import models


# Create your models here.
class product(models.Model):
    p_id = models.CharField(max_length=20, primary_key=True)
    brand = models.CharField(max_length=20)
    p_name = models.CharField(max_length=50)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=False)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=False)
    qty = models.IntegerField(default=0)
    type_choices = [("by_qty","by quantity"),("by_wt","by weight")]
    type = models.CharField(max_length=20, choices=type_choices, default="by_qty")

    def __str__(self):
        return self.p_id

class transaction(models.Model):
    t_id = models.AutoField(primary_key=True)
    # t_date = models.DateTimeField(auto_now_add=True, null=True)
    t_date = models.CharField(max_length=10, default = "2022/04/03", null=True)
    
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=False)
    profit = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=False)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=False)

    customer_id = models.IntegerField(null = True)
    

class sold_product(models.Model):
    ps_id = models.AutoField(primary_key=True, default=0)
    tran_id = models.IntegerField(default=0)
    # t_date = models.DateTimeField(auto_now_add=True, null=True)
    t_date = models.CharField(max_length=20, default = "2022/04/03")

    prod = models.ForeignKey(product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=False)
    item_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=False)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=False)
    net_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=False)
    profit = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=False)
    