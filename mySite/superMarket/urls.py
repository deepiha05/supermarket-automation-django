"""mySite URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from superMarket import views

urlpatterns = [
    path("", views.first_page,  name='home'),
    path("logoutUser", views.logoutUser,  name='logoutUser'),
    
    path("manager_login", views.manager_login,  name='manager_login'),
    path("manager_signup", views.manager_signup,  name='manager_signup'),
    path("manager_page1", views.manager_page1,  name='manager_page1'),
    path("manager_inventory", views.manager_inventory,  name='manager_inventory'),
    path("manager_changePrice", views.manager_changePrice,  name='manager_changePrice'),
    path("manager_viewStat", views.manager_viewStat,  name='manager_viewStat'),
    path("manager_saleStat_profit", views.saleStat_profit,  name='manager_saleStat_profit'),
    path("manager_salesStat_qty", views.salesStat_qty,  name='manager_salesStat_qty'),
    path("manager_salesStat_net", views.salesStat_net,  name='manager_salesStat_net'),

    path("employee_login", views.employee_login,  name='employee_login'),
    path("employee_signup", views.employee_signup,  name='employee_signup'),
    path("employee_page1", views.employee_page1,  name='employee_page1'),
    path("employee_addProduct", views.employee_addProduct,  name='employee_addProduct'),
    path("employee_updateStock", views.employee_updateStock,  name='employee_updateStock'),


    path("salesClerk_signup", views.salesClerk_signup,  name='salesClerk_signup'),
    path("salesClerk_login", views.salesClerk_login,  name='salesClerk_login'),
    path("salesClerk_page1", views.salesClerk_page1,  name='salesClerk_page1'),
    path("salesClerk_billing", views.salesClerk_billing,  name='salesClerk_billing'),
    path("salesClerk_generateBill", views.salesClerk_generateBill,  name='salesClerk_genBill'),
]
