"""
One-shot setup command for grading/reviewing.

Run this once after migrating:

    python manage.py bootstrap_demo

It creates:
  - the Manager and Delivery crew groups
  - one manager user, one delivery-crew user, one plain customer user
  - a couple of categories and menu items so the browsing endpoints return data

It does NOT create the superuser — create that yourself with
`python manage.py createsuperuser` so only you know that password.
"""

from django.contrib.auth.models import User, Group
from django.core.management.base import BaseCommand

from LittleLemonAPI.models import Category, MenuItem


class Command(BaseCommand):
    help = 'Creates demo groups, users, and menu data for the Little Lemon API.'

    def handle(self, *args, **options):
        manager_group, _ = Group.objects.get_or_create(name='Manager')
        delivery_group, _ = Group.objects.get_or_create(name='Delivery crew')
        self.stdout.write(self.style.SUCCESS('Groups ready: Manager, Delivery crew'))

        demo_users = [
            ('manager1', 'ManagerPass123!', manager_group),
            ('delivery1', 'DeliveryPass123!', delivery_group),
            ('customer1', 'CustomerPass123!', None),
        ]

        for username, password, group in demo_users:
            user, created = User.objects.get_or_create(username=username)
            if created:
                user.set_password(password)
                user.email = f'{username}@example.com'
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Created user: {username}'))
            if group:
                group.user_set.add(user)

        categories = {
            'appetizers': 'Appetizers',
            'main-courses': 'Main Courses',
            'desserts': 'Desserts',
            'beverages': 'Beverages',
        }
        cat_objs = {}
        for slug, title in categories.items():
            cat, _ = Category.objects.get_or_create(slug=slug, defaults={'title': title})
            cat_objs[slug] = cat

        menu_items = [
            ('Greek Salad', '12.99', True, 'appetizers'),
            ('Bruschetta', '7.99', False, 'appetizers'),
            ('Grilled Fish', '20.00', True, 'main-courses'),
            ('Lemon Chicken', '16.50', False, 'main-courses'),
            ('Lemon Cake', '6.50', False, 'desserts'),
            ('Baklava', '5.50', False, 'desserts'),
            ('Iced Tea', '3.00', False, 'beverages'),
        ]
        for title, price, featured, cat_slug in menu_items:
            MenuItem.objects.get_or_create(
                title=title,
                defaults={'price': price, 'featured': featured, 'category': cat_objs[cat_slug]},
            )

        self.stdout.write(self.style.SUCCESS('Demo users and menu data created.'))
        self.stdout.write('  manager1  / ManagerPass123!')
        self.stdout.write('  delivery1 / DeliveryPass123!')
        self.stdout.write('  customer1 / CustomerPass123!')
