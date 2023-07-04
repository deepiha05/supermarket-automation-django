import sqlite3
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.forms import inlineformset_factory
from matplotlib.style import context

import matplotlib.pyplot as plt

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import Group, User

from django.contrib.auth.decorators import login_required
import superMarket
from superMarket.decorators import unauthenticated_manager, unauthenticated_employee, unauthenticated_salesClerk
from superMarket.decorators import allowed_users
# Create your views here.
from superMarket.models import *
from superMarket.forms import createUserForm, addProductForm

def first_page(request):
    return render(request, 'home_page.html')

def logoutUser(request):
    logout(request)
    return redirect('/')


def manager_signup(request):
    form = createUserForm()
    if request.method == 'POST':
        form = createUserForm(request.POST)
        if form.is_valid():
            form.save()
            
            usrnm = form.cleaned_data.get('username')
            # user = User.objects.get(username = usrnm)
            # group = Group.objects.get(name='Managers')
            # user.groups.add(group)
            messages.success(request, 'Manager Account '+usrnm+' created')

            return redirect('/manager_login')

    context = {'form':form}
    return render(request, 'register.html', context)
    # return render(request, 'manager_signup.html')

@unauthenticated_manager
def manager_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/manager_page1')
        else:
            messages.info(request, 'Incorrect Credentials !!')

    context = {}
    # return render(request, 'm_login.html', context)
    return render(request, 'manager_login.html', context)


@allowed_users(allowed_roles=['Managers'])
@login_required(login_url='/manager_login')
def manager_page1(request):
    return render(request, 'manager1.html')

@allowed_users(allowed_roles=['Managers'])
@login_required(login_url='/manager_login')
def manager_inventory(request):
    if request.method == 'POST':
        global p_obj, p_id_in
        p_id_in = request.POST.get('p_id_in')
        try:
            p_obj = product.objects.get(p_id = p_id_in)
        except product.DoesNotExist:
            p_obj = None
            return redirect('/manager_inventory')
        return redirect('/manager_changePrice')
    p_list = product.objects.all().order_by('brand')
    context = {
        "p_list":p_list
    }
    return render(request,'manager_inventory.html', context)

@allowed_users(allowed_roles=['Managers'])
@login_required(login_url='/manager_login')
def manager_changePrice(request):
    global p_id_in
    p_obj = None
    try:
        p_obj = product.objects.get(p_id = p_id_in)
    except product.DoesNotExist:
        p_id_in = None
        return redirect('/manager_inventory')

    if p_obj is None:
        return redirect('/manager_inventory')

    context={
        "p_id" : p_obj.p_id ,
        "brand" : p_obj.brand ,
        "p_name" : p_obj.p_name ,
        "cost_price" : p_obj.cost_price ,
        "price" : p_obj.price ,
        "qty" : p_obj.qty ,
        "type" : p_obj.type ,
    }
    if request.method == 'POST':
        newPrice = int(request.POST.get('newPrice'))
        # print(p_obj.qty, newVal)
        p_obj.price = newPrice
        p_obj.save()
        # print(p_obj.qty)
        return redirect('/manager_inventory')

    return render(request, 'edit_price.html',context)

@allowed_users(allowed_roles=['Managers'])
@login_required(login_url='/manager_login')
def manager_viewStat(request):
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        stat_type = request.POST.get('stat_type')

        pl =[]
        for obj in  sold_product.objects.all():
            if obj.t_date > start_date and obj.t_date < end_date:
                pl.append(obj)
        
        prods = []
        sold_qty = {}
        sold_profit = {}
        for obj in pl:
            if obj.prod.p_id in prods:
                sold_qty[obj.prod.p_id] += obj.quantity
                sold_profit[obj.prod.p_id] += obj.profit
            else:
                prods.append(obj.prod.p_id)
                sold_qty[obj.prod.p_id] = obj.quantity
                sold_profit[obj.prod.p_id] = obj.profit
        
        y_qty = []
        y_profit = []
        for x in prods:
            y_qty.append( sold_qty[x] )
            y_profit.append( sold_profit[x] )
        
        
        plt.plot(prods, y_qty) 
        plt.xlabel('Product id')
        plt.ylabel('Quantity sold')
 
        plt.title('Item vs quantity')
        plt.show()
        plt.savefig('/home/subha/codes/SAS/mySite/static/item_qty.png')

        plt.plot(prods, y_profit) 
        plt.xlabel('Product id')
        plt.ylabel('Profit from product')
 
        plt.title('Item vs profit')
        plt.show()
        plt.savefig('/home/subha/codes/SAS/mySite/static/item_profit.png')

        if stat_type == "item_qty":
            return redirect('/manager_saleStat_qty')
        elif stat_type == "item_profit":
            return redirect('/manager_saleStat_profit')
        else:
            return redirect('/manager_salesStat_net')

    context = {}
    return render(request, 'sales_statistics.html', context)

@allowed_users(allowed_roles=['Managers'])
@login_required(login_url='/manager_login')
def saleStat_profit(request):

    return render(request, 'item_vs_profit.html')

@allowed_users(allowed_roles=['Managers'])
@login_required(login_url='/manager_login')
def salesStat_qty(request):

    return render(request, 'item_vs_qty.html')

@allowed_users(allowed_roles=['Managers'])
@login_required(login_url='/manager_login')
def salesStat_net(request):

    return render(request, 'net_sales.html')

def employee_signup(request):
    form = createUserForm()
    if request.method == 'POST':
        form = createUserForm(request.POST)
        if form.is_valid():
            form.save()
            usrnm = form.cleaned_data.get('username')
            messages.success(request, 'Employee Account '+usrnm+' created')

            return redirect('/employee_login')

    context = {'form':form}
    return render(request, 'register.html', context)

@unauthenticated_employee
def employee_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/employee_page1')
        else:
            messages.info(request, 'Incorrect Credentials !!')

    context = {}
    return render(request, 'employee_login.html', context)

p_id_in = None

@allowed_users(allowed_roles=['Employees', 'Managers'])
@login_required(login_url='/employee_login')
def employee_page1(request):
    if request.method == 'POST':
        global p_id_in
        p_id_in = request.POST.get('p_id_in')
        p_obj = None
        try:
            p_obj = product.objects.get(p_id = p_id_in)
        except product.DoesNotExist:
            p_id_in = None
            return redirect('/employee_page1')
        return redirect('/employee_updateStock')
    
    p_list = product.objects.all().order_by('brand')
    context = {
        "p_list":p_list
    }

    return render(request, 'employee1.html', context)

@allowed_users(allowed_roles=['Employees', 'Managers'])
@login_required(login_url='/employee_login')
def employee_addProduct(request):
    form = addProductForm()
    if request.method == 'POST':
        # print('Printing POST: ',request.POST)
        form = addProductForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/employee_page1')
        pass

    context = {'form':form}
    return render(request, 'addnewproduct.html', context)


@allowed_users(allowed_roles=['Employees', 'Managers'])
@login_required(login_url='/employee_login')
def employee_updateStock(request):
    global p_id_in
    p_obj = None
    try:
        p_obj = product.objects.get(p_id = p_id_in)
    except product.DoesNotExist:
        p_id_in = None
        return redirect('/employee_page1')

    if p_obj is None:
        return redirect('/employee_page1')

    context={
        "p_id" : p_obj.p_id ,
        "brand" : p_obj.brand ,
        "p_name" : p_obj.p_name ,
        "cost_price" : p_obj.cost_price ,
        "price" : p_obj.price ,
        "qty" : p_obj.qty ,
        "type" : p_obj.type ,
    }

    if request.method == 'POST':
        newVal = int(request.POST.get('qtyImport'))
        # print(p_obj.qty, newVal)
        p_obj.qty = p_obj.qty + newVal
        p_obj.save()
        # print(p_obj.qty)
        return redirect('/employee_page1')

    return render(request, 'edit_quantity.html', context)


def salesClerk_signup(request):
    form = createUserForm()
    if request.method == 'POST':
        form = createUserForm(request.POST)
        if form.is_valid():
            form.save()
            usrnm = form.cleaned_data.get('username')
            messages.success(request, 'SalesClerk Account '+usrnm+' created')

            return redirect('/salesClerk_login')

    context = {'form':form}
    return render(request, 'register.html', context)

@unauthenticated_salesClerk
def salesClerk_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/salesClerk_page1')
        else:
            messages.info(request, 'Incorrect Credentials !!')

    context = {}
    return render(request, 'salesClerk_login.html', context)

transaction_id = 1
tran_date = None
ps_id = 1
c_id = None


# @allowed_users(allowed_roles=['SalesClerk','Employees'])
@login_required(login_url='/salesClerk_login')
def salesClerk_page1(request):
    global c_id, tran_date
    if request.method == 'POST':
        c_id = int(request.POST.get('c_id'))
        tran_date = request.POST.get('t_date')

        return redirect('salesClerk_billing')

    context = {}
    return render(request, 'salesClerk1.html', context)


# @allowed_users(allowed_roles=['SalesClerk','Employees'])
@login_required(login_url='/salesClerk_login')
def salesClerk_billing(request):
    if request.method == 'POST':
        p_id = request.POST.get('p_id_in')
        qty = int(request.POST.get('qty_in'))

        p_obj = None
        try:
            p_obj = product.objects.get(p_id = p_id)
        except product.DoesNotExist:
            # p_id = None
            return redirect('/salesClerk_billing')
        
        global transaction_id, ps_list, ps_id, tran_date
        p = product.objects.get(p_id = p_id)
        s_price = float(p.price)
        c_price = float(p.cost_price)
        ps = sold_product(
            ps_id = ps_id,
            tran_id = transaction_id,
            prod = p,
            quantity = qty,
            unit_price = p.price,
            item_price = s_price*float(qty),
            tax = round(s_price*float(qty)*0.05, 2),
            net_cost = round(s_price*float(qty)*1.05, 2),
            profit = round((s_price - c_price)*float(qty), 2),
        )
        ps.save()
        ps_id = ps_id+1

        p.qty = p.qty - qty
        p.save()
        return redirect('/salesClerk_billing')
    
    print(transaction_id, tran_date)
    ps_list = sold_product.objects.all().filter(tran_id = transaction_id)
    context = {
        "p_list":ps_list
    }

    return render(request, 'billing.html', context)

@login_required(login_url='/salesClerk_login')
def salesClerk_generateBill(request):
    global transaction_id, c_id
    
    total_bill_cost = 0
    net_profit = 0
    net_tax = 0
    ps_list = sold_product.objects.all().filter(tran_id = transaction_id)
    for obj in ps_list:
        total_bill_cost += obj.net_cost
        net_profit += obj.profit
        net_tax += obj.tax
    
    print("1 generating bill")
    T = transaction(
        t_date = tran_date,
        total_cost = total_bill_cost,
        profit = net_profit,
        tax = net_tax,
        customer_id = c_id
    )
    T.save()

    print(transaction_id)
    print("2 generating bill")

    context = {
        "p_list":ps_list,
        "T":T,
    }

    
    transaction_id = transaction_id + 1
    ps_list = sold_product.objects.none()
    c_id = None

    print(transaction_id)
    print("3 generating bill")

    return render(request, 'final_bill.html', context)