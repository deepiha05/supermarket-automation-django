from django.db import migrations

ROLES = ['Managers', 'Employees', 'SalesClerk']


def create_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    for name in ROLES:
        Group.objects.get_or_create(name=name)


def remove_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name__in=ROLES).delete()


class Migration(migrations.Migration):
    """Creates the three user roles that the views check for."""

    dependencies = [
        ('superMarket', '0003_sold_product_autoincrement'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(create_groups, remove_groups),
    ]
