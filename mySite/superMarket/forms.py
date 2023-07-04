from dataclasses import field
from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from superMarket.models import product, transaction


class createUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'password1', 'password2']

class addProductForm(ModelForm):
    class Meta:
        model = product
        fields = '__all__'
        