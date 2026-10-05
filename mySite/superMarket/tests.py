import os
import tempfile
from decimal import Decimal
from unittest import mock

from django.contrib.auth.models import Group, User
from django.test import TestCase

from superMarket import views
from superMarket.models import product, sold_product, transaction

PASSWORD = 'Xx-12345-pass'


def make_user(username, role=None, **kwargs):
    user = User.objects.create_user(username, password=PASSWORD, **kwargs)
    if role:
        user.groups.add(Group.objects.get(name=role))
    return user


class SasTestCase(TestCase):
    fixtures = ['sample_products']

    def client_for(self, username, role=None):
        make_user(username, role)
        self.client.login(username=username, password=PASSWORD)
        return self.client

    def start_bill(self, client, customer='9000000001', date='2022/04/05'):
        return client.post('/salesClerk_page1', {'c_id': customer, 't_date': date})

    def add_item(self, client, p_id, qty):
        return client.post('/salesClerk_billing', {'p_id_in': p_id, 'qty_in': str(qty)})


class RoleTests(SasTestCase):
    def test_roles_exist_after_migrations(self):
        self.assertEqual(set(Group.objects.values_list('name', flat=True)),
                         {'Managers', 'Employees', 'SalesClerk'})

    def test_signup_assigns_role(self):
        for url, role in [('/manager_signup', 'Managers'), ('/employee_signup', 'Employees'),
                          ('/salesClerk_signup', 'SalesClerk')]:
            username = 'new_' + role.lower()
            self.client.post(url, {'username': username, 'first_name': 'N',
                                   'password1': PASSWORD, 'password2': PASSWORD})
            self.assertEqual(list(User.objects.get(username=username).groups.values_list('name', flat=True)), [role])

    def test_new_manager_can_open_manager_page(self):
        self.client.post('/manager_signup', {'username': 'm', 'first_name': 'M',
                                             'password1': PASSWORD, 'password2': PASSWORD})
        self.client.login(username='m', password=PASSWORD)
        self.assertEqual(self.client.get('/manager_page1').status_code, 200)

    def test_anonymous_user_is_sent_to_login(self):
        response = self.client.get('/salesClerk_billing')
        self.assertRedirects(response, '/salesClerk_login?next=/salesClerk_billing', fetch_redirect_response=False)

    def test_user_without_role_is_refused(self):
        client = self.client_for('nobody')
        for url in ['/manager_page1', '/employee_page1', '/salesClerk_page1', '/salesClerk_billing']:
            self.assertEqual(client.get(url).status_code, 403, url)

    def test_clerk_cannot_open_manager_pages(self):
        client = self.client_for('clerk', 'SalesClerk')
        self.assertEqual(client.get('/manager_inventory').status_code, 403)

    def test_superuser_can_open_every_page(self):
        User.objects.create_superuser('admin', password=PASSWORD)
        self.client.login(username='admin', password=PASSWORD)
        for url in ['/manager_page1', '/employee_page1', '/salesClerk_page1']:
            self.assertEqual(self.client.get(url).status_code, 200, url)


class BillingTests(SasTestCase):
    def test_full_bill(self):
        client = self.client_for('clerk', 'SalesClerk')
        self.start_bill(client)
        self.add_item(client, 'ASDF', 2)   # 2 x 40000
        self.add_item(client, 'FGHJ', 1)   # 1 x 25000
        response = client.get('/salesClerk_generateBill')

        T = response.context['T']
        self.assertEqual(T.total_cost, Decimal('110250.00'))   # 105000 + 5% tax
        self.assertEqual(T.tax, Decimal('5250.00'))
        self.assertEqual(T.profit, Decimal('25000.00'))        # 2 x 10000 + 1 x 5000
        self.assertEqual(T.customer_id, 9000000001)
        self.assertEqual(product.objects.get(p_id='ASDF').qty, 378)
        self.assertEqual(product.objects.get(p_id='FGHJ').qty, 29)
        self.assertEqual(set(sold_product.objects.values_list('t_date', flat=True)), {'2022/04/05'})

    def test_bills_do_not_share_items(self):
        client = self.client_for('clerk', 'SalesClerk')
        self.start_bill(client, customer='1')
        self.add_item(client, 'ASDF', 1)
        client.get('/salesClerk_generateBill')

        self.start_bill(client, customer='2')
        self.add_item(client, 'QWER', 3)
        response = client.get('/salesClerk_generateBill')
        self.assertEqual([(p.prod_id, p.quantity) for p in response.context['p_list']], [('QWER', 3)])

    def test_billing_works_with_existing_sales(self):
        # Rows already in the table (as after a server restart) must not clash with new ones
        sold_product.objects.create(tran_id=999, prod_id='ASDF', quantity=1)
        client = self.client_for('clerk', 'SalesClerk')
        self.start_bill(client)
        self.add_item(client, 'ASDF', 1)
        self.assertEqual(sold_product.objects.count(), 2)

    def test_two_clerks_have_separate_bills(self):
        make_user('a', 'SalesClerk')
        make_user('b', 'SalesClerk')
        a, b = self.client_class(), self.client_class()
        a.login(username='a', password=PASSWORD)
        b.login(username='b', password=PASSWORD)
        self.start_bill(a, customer='1')
        self.start_bill(b, customer='2')
        self.add_item(a, 'ASDF', 1)
        self.add_item(b, 'QWER', 2)
        self.assertEqual([p.prod_id for p in a.get('/salesClerk_billing').context['p_list']], ['ASDF'])
        self.assertEqual([p.prod_id for p in b.get('/salesClerk_billing').context['p_list']], ['QWER'])

    def test_cannot_sell_more_than_stock(self):
        client = self.client_for('clerk', 'SalesClerk')
        self.start_bill(client)
        self.add_item(client, 'FGHJ', 31)   # only 30 in stock
        self.assertEqual(sold_product.objects.count(), 0)
        self.assertEqual(product.objects.get(p_id='FGHJ').qty, 30)

    def test_invalid_quantity_and_product_are_rejected(self):
        client = self.client_for('clerk', 'SalesClerk')
        self.start_bill(client)
        self.add_item(client, 'ASDF', 0)
        self.add_item(client, 'NOPE', 1)
        client.post('/salesClerk_billing', {'p_id_in': 'ASDF', 'qty_in': 'abc'})
        self.assertEqual(sold_product.objects.count(), 0)

    def test_invalid_customer_or_date_shows_form_again(self):
        client = self.client_for('clerk', 'SalesClerk')
        self.assertEqual(self.start_bill(client, customer='abc').status_code, 200)
        self.assertEqual(self.start_bill(client, date='5th April').status_code, 200)
        self.assertEqual(transaction.objects.count(), 0)

    def test_billing_without_a_started_bill_goes_back(self):
        client = self.client_for('clerk', 'SalesClerk')
        self.assertRedirects(client.get('/salesClerk_billing'), '/salesClerk_page1', fetch_redirect_response=False)


class InventoryTests(SasTestCase):
    def test_employee_updates_stock(self):
        client = self.client_for('emp', 'Employees')
        client.post('/employee_page1', {'p_id_in': 'QWER'})
        client.post('/employee_updateStock', {'qtyImport': '5'})
        self.assertEqual(product.objects.get(p_id='QWER').qty, 55)

    def test_employee_adds_product(self):
        client = self.client_for('emp', 'Employees')
        client.post('/employee_addProduct', {'p_id': 'ZXCV', 'brand': 'Nokia', 'p_name': '3310',
                                             'cost_price': '1000', 'price': '1500', 'qty': '10', 'type': 'by_qty'})
        self.assertTrue(product.objects.filter(p_id='ZXCV').exists())

    def test_manager_changes_price(self):
        client = self.client_for('mgr', 'Managers')
        client.post('/manager_inventory', {'p_id_in': 'FGHJ'})
        client.post('/manager_changePrice', {'newPrice': '27000'})
        self.assertEqual(product.objects.get(p_id='FGHJ').price, Decimal('27000.00'))


class StatisticsTests(SasTestCase):
    def setUp(self):
        self.chart_dir = tempfile.mkdtemp()
        patcher = mock.patch.object(views, 'CHART_DIR', self.chart_dir)
        patcher.start()
        self.addCleanup(patcher.stop)

        for date, p_id, qty in [('2022/04/01', 'ASDF', 2), ('2022/04/05', 'ASDF', 3),
                                ('2022/04/10', 'QWER', 1), ('2022/05/01', 'FGHJ', 7)]:
            sold_product.objects.create(t_date=date, prod_id=p_id, quantity=qty, profit=qty * 100)

    def test_statistics_are_generated_for_inclusive_range(self):
        client = self.client_for('mgr', 'Managers')
        with mock.patch.object(views, 'save_chart') as save_chart:
            client.post('/manager_viewStat', {'start_date': '2022/04/01', 'end_date': '2022-04-10',
                                              'stat_type': 'item_qty'})
        qty_call = save_chart.call_args_list[0][0]
        self.assertEqual(qty_call[0], ['ASDF', 'QWER'])   # May sale excluded, both end days included
        self.assertEqual(qty_call[1], [5, 1])

    def test_each_statistic_page_opens_with_its_chart(self):
        client = self.client_for('mgr', 'Managers')
        for stat_type in ['item_qty', 'item_profit', 'net']:
            response = client.post('/manager_viewStat', {'start_date': '2022/01/01', 'end_date': '2022/12/31',
                                                         'stat_type': stat_type})
            self.assertEqual(client.get(response['Location']).status_code, 200, stat_type)
        for name in ['item_qty.png', 'item_profit.png']:
            self.assertTrue(os.path.getsize(os.path.join(self.chart_dir, name)) > 0)

    def test_invalid_dates_show_form_again(self):
        client = self.client_for('mgr', 'Managers')
        response = client.post('/manager_viewStat', {'start_date': 'yesterday', 'end_date': '2022/12/31',
                                                     'stat_type': 'net'})
        self.assertEqual(response.status_code, 200)


class ParseDateTests(TestCase):
    def test_formats(self):
        self.assertEqual(views.parse_date('2022/4/5'), '2022/04/05')
        self.assertEqual(views.parse_date(' 2022 / 04 / 05 '), '2022/04/05')
        self.assertEqual(views.parse_date('2022-04-05'), '2022/04/05')
        self.assertIsNone(views.parse_date('2022/13/01'))
        self.assertIsNone(views.parse_date('April 5'))
        self.assertIsNone(views.parse_date(None))
