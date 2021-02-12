from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group


class Command(BaseCommand):
    help = 'Add Default Groups'

    def handle(self, *args, **options):
        g_list = [
            'Staff', 'Customer',
        ]
        for grp_name in g_list:
            grp, created = Group.objects.get_or_create(name=grp_name)
        print("Default groups created.")