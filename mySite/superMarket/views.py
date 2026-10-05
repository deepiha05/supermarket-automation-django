import os
import re
from collections import OrderedDict

import matplotlib
matplotlib.use("Agg")  # render charts to files; there is no display in a web server
import matplotlib.pyplot as plt

from django.conf import settings
from django.shortcuts import render, redirect

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import Group

from django.contrib.auth.decorators import login_required
from superMarket.decorators import unauthenticated_manager, unauthenticated_employee, unauthenticated_salesClerk
from superMarket.decorators import allowed_users
# Create your views here.
from superMarket.models import product, transaction, sold_product
from superMarket.forms import createUserForm, addProductForm

TAX_RATE = 0.05
CHART_DIR = os.path.join(settings.BASE_DIR, "static")


def parse_date(text):
    """
    Accepts dates like "2022/04/05", "2022 / 04 / 05" or "2022-04-05" and
    returns them as "YYYY/MM/DD" (the format stored in the database), or None.
    """
    m = re.fullmatch(r"\s*(\d{4})\s*[/-]\s*(\d{1,2})\s*[/-]\s*(\d{1,2})\s*", text or "")
    if not m:
        return None
    year, month, day = (int(g) for g in m.groups())
    if not (1 <= month <= 12 and 1 <= day <= 31):
        return None
    return f"{year:04d}/{month:02d}/{day:02d}"


def first_page(request):
    return render(request, 'home_page.html')

def logoutUser(request):
    logout(request)
    return redirect('/')


def signup(request, group_name, role, login_url):
    """Shared sign-up view: creates the user and adds them to `group_name`."""
    form = createUserForm()
    if request.method == 'POST':
        form = createUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            group, _ = Group.objects.get_or_create(name=group_name)
            user.groups.add(group)

            usrnm = form.cleaned_data.get('username')
            messages.success(request, role + ' Account ' + usrnm + ' created')

            return redirect(login_url)

    context = {'form': form, 'login_url': login_url}
    return render(request, 'register.html', context)


def manager_signup(request):
    return signup(request, 'Managers', 'Manager', '/manager_login')

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
    return render(request, 'manager_login.html', context)


@login_required(login_url='/manager_login')
@allowed_users(allowed_roles=['Managers'])
def manager_page1(request):
    return render(request, 'manager1.html')

@login_required(login_url='/manager_login')
@allowed_users(allowed_roles=['Managers'])
def manager_inventory(request):
    if request.method == 'POST':
        p_id_in = request.POST.get('p_id_in')
        if not product.objects.filter(p_id=p_id_in).exists():
            return redirect('/manager_inventory')
        request.session['price_p_id'] = p_id_in  # product whose price is being edited
        return redirect('/manager_changePrice')
    p_list = product.objects.all().order_by('brand')
    context = {
        "p_list":p_list
    }
    return render(request,'manager_inventory.html', context)

@login_required(login_url='/manager_login')
@allowed_users(allowed_roles=['Managers'])
def manager_changePrice(request):
    try:
        p_obj = product.objects.get(p_id=request.session.get('price_p_id'))
    except product.DoesNotExist:
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
        try:
            newPrice = int(request.POST.get('newPrice'))
        except (TypeError, ValueError):
            return render(request, 'edit_price.html', context)
        if newPrice >= 0:
            p_obj.price = newPrice
            p_obj.save()
        request.session.pop('price_p_id', None)
        return redirect('/manager_inventory')

    return render(request, 'edit_price.html',context)


def save_chart(x, y, ylabel, title, filename):
    """Draws a bar chart on a fresh figure and saves it in the static folder."""
    fig = plt.figure()
    plt.bar([str(v) for v in x], [float(v) for v in y])
    plt.xlabel('Product id')
    plt.ylabel(ylabel)
    plt.title(title if x else title + ' (no sales in this period)')
    fig.savefig(os.path.join(CHART_DIR, filename))
    plt.close(fig)


@login_required(login_url='/manager_login')
@allowed_users(allowed_roles=['Managers'])
def manager_viewStat(request):
    if request.method == 'POST':
        start_date = parse_date(request.POST.get('start_date'))
        end_date = parse_date(request.POST.get('end_date'))
        stat_type = request.POST.get('stat_type')

        if start_date is None or end_date is None:
            messages.error(request, 'Please enter both dates as YYYY/MM/DD.')
            return render(request, 'sales_statistics.html', {})

        # quantity sold and profit per product, for sales within the period (inclusive)
        sold_qty = OrderedDict()
        sold_profit = OrderedDict()
        for obj in sold_product.objects.select_related('prod').order_by('prod__p_id'):
            if start_date <= obj.t_date <= end_date:
                p_id = obj.prod.p_id
                sold_qty[p_id] = sold_qty.get(p_id, 0) + obj.quantity
                sold_profit[p_id] = sold_profit.get(p_id, 0) + obj.profit

        prods = list(sold_qty)
        save_chart(prods, [sold_qty[p] for p in prods], 'Quantity sold', 'Item vs quantity', 'item_qty.png')
        save_chart(prods, [sold_profit[p] for p in prods], 'Profit from product', 'Item vs profit', 'item_profit.png')

        if stat_type == "item_qty":
            return redirect('/manager_salesStat_qty')
        elif stat_type == "item_profit":
            return redirect('/manager_saleStat_profit')
        else:
            return redirect('/manager_salesStat_net')

    context = {}
    return render(request, 'sales_statistics.html', context)

@login_required(login_url='/manager_login')
@allowed_users(allowed_roles=['Managers'])
def saleStat_profit(request):

    return render(request, 'item_vs_profit.html')

@login_required(login_url='/manager_login')
@allowed_users(allowed_roles=['Managers'])
def salesStat_qty(request):

    return render(request, 'item_vs_qty.html')

@login_required(login_url='/manager_login')
@allowed_users(allowed_roles=['Managers'])
def salesStat_net(request):

    return render(request, 'net_sales.html')

def employee_signup(request):
    return signup(request, 'Employees', 'Employee', '/employee_login')

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


@login_required(login_url='/employee_login')
@allowed_users(allowed_roles=['Employees', 'Managers'])
def employee_page1(request):
    if request.method == 'POST':
        p_id_in = request.POST.get('p_id_in')
        if not product.objects.filter(p_id=p_id_in).exists():
            return redirect('/employee_page1')
        request.session['stock_p_id'] = p_id_in  # product whose stock is being updated
        return redirect('/employee_updateStock')

    p_list = product.objects.all().order_by('brand')
    context = {
        "p_list":p_list
    }

    return render(request, 'employee1.html', context)

@login_required(login_url='/employee_login')
@allowed_users(allowed_roles=['Employees', 'Managers'])
def employee_addProduct(request):
    form = addProductForm()
    if request.method == 'POST':
        form = addProductForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/employee_page1')

    context = {'form':form}
    return render(request, 'addnewproduct.html', context)


@login_required(login_url='/employee_login')
@allowed_users(allowed_roles=['Employees', 'Managers'])
def employee_updateStock(request):
    try:
        p_obj = product.objects.get(p_id=request.session.get('stock_p_id'))
    except product.DoesNotExist:
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
        try:
            newVal = int(request.POST.get('qtyImport'))
        except (TypeError, ValueError):
            return render(request, 'edit_quantity.html', context)
        if newVal > 0:
            p_obj.qty = p_obj.qty + newVal
            p_obj.save()
        request.session.pop('stock_p_id', None)
        return redirect('/employee_page1')

    return render(request, 'edit_quantity.html', context)


def salesClerk_signup(request):
    return signup(request, 'SalesClerk', 'SalesClerk', '/salesClerk_login')

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


def current_transaction(request):
    """The bill this sales clerk is working on (kept in their session), or None."""
    try:
        return transaction.objects.get(t_id=request.session.get('tran_id'))
    except transaction.DoesNotExist:
        return None


@login_required(login_url='/salesClerk_login')
@allowed_users(allowed_roles=['SalesClerk', 'Managers'])
def salesClerk_page1(request):
    if request.method == 'POST':
        try:
            c_id = int(request.POST.get('c_id'))
        except (TypeError, ValueError):
            messages.error(request, 'Please enter the customer number using digits only.')
            return render(request, 'salesClerk1.html', {})
        tran_date = parse_date(request.POST.get('t_date'))
        if tran_date is None:
            messages.error(request, 'Please enter the date as YYYY/MM/DD.')
            return render(request, 'salesClerk1.html', {})

        # Drop a bill that was started but never had any item added
        old = current_transaction(request)
        if old is not None and not sold_product.objects.filter(tran_id=old.t_id).exists():
            old.delete()

        T = transaction.objects.create(t_date=tran_date, customer_id=c_id)
        request.session['tran_id'] = T.t_id
        return redirect('salesClerk_billing')

    context = {}
    return render(request, 'salesClerk1.html', context)


@login_required(login_url='/salesClerk_login')
@allowed_users(allowed_roles=['SalesClerk', 'Managers'])
def salesClerk_billing(request):
    T = current_transaction(request)
    if T is None:  # no bill started yet
        return redirect('/salesClerk_page1')

    if request.method == 'POST':
        p_id = request.POST.get('p_id_in')
        try:
            qty = int(request.POST.get('qty_in'))
        except (TypeError, ValueError):
            qty = 0

        try:
            p = product.objects.get(p_id = p_id)
        except product.DoesNotExist:
            messages.error(request, 'No product with id ' + str(p_id) + '.')
            return redirect('/salesClerk_billing')

        if qty <= 0:
            messages.error(request, 'Quantity must be a positive number.')
            return redirect('/salesClerk_billing')
        if qty > p.qty:
            messages.error(request, 'Only ' + str(p.qty) + ' of ' + p.p_id + ' in stock.')
            return redirect('/salesClerk_billing')

        s_price = float(p.price)
        c_price = float(p.cost_price)
        sold_product.objects.create(
            tran_id = T.t_id,
            t_date = T.t_date,
            prod = p,
            quantity = qty,
            unit_price = p.price,
            item_price = s_price*float(qty),
            tax = round(s_price*float(qty)*TAX_RATE, 2),
            net_cost = round(s_price*float(qty)*(1 + TAX_RATE), 2),
            profit = round((s_price - c_price)*float(qty), 2),
        )

        p.qty = p.qty - qty
        p.save()
        return redirect('/salesClerk_billing')

    ps_list = sold_product.objects.filter(tran_id = T.t_id)
    context = {
        "p_list":ps_list
    }

    return render(request, 'billing.html', context)

@login_required(login_url='/salesClerk_login')
@allowed_users(allowed_roles=['SalesClerk', 'Managers'])
def salesClerk_generateBill(request):
    T = current_transaction(request)
    if T is None:
        return redirect('/salesClerk_page1')

    total_bill_cost = 0
    net_profit = 0
    net_tax = 0
    ps_list = sold_product.objects.filter(tran_id = T.t_id)
    for obj in ps_list:
        total_bill_cost += obj.net_cost
        net_profit += obj.profit
        net_tax += obj.tax

    T.total_cost = total_bill_cost
    T.profit = net_profit
    T.tax = net_tax
    T.save()

    context = {
        "p_list":ps_list,
        "T":T,
    }

    # The bill is finished; the next customer starts a new one
    request.session.pop('tran_id', None)

    return render(request, 'final_bill.html', context)
