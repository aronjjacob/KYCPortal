from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User, Group


class Command(BaseCommand):
    help = 'Assign roles (client/verifier) to users.'

    def add_arguments(self, parser):
        parser.add_argument(
            'username',
            type=str,
            help='Username to assign role to'
        )
        parser.add_argument(
            'role',
            type=str,
            choices=['client', 'verifier'],
            help='Role to assign (client or verifier)'
        )
        parser.add_argument(
            '--remove',
            action='store_true',
            help='Remove role instead of assigning'
        )
        parser.add_argument(
            '--clear-all',
            action='store_true',
            help='Clear all roles before assigning new one'
        )

    def handle(self, *args, **options):
        username = options['username']
        role = options['role']
        remove = options['remove']
        clear_all = options['clear_all']

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f'User "{username}" does not exist.')

        try:
            group = Group.objects.get(name=role)
        except Group.DoesNotExist:
            raise CommandError(f'Group "{role}" does not exist. Create groups using the admin or app ready signal.')

        if clear_all:
            user.groups.clear()
            self.stdout.write(self.style.WARNING(f'Cleared all roles from {username}'))

        if remove:
            user.groups.remove(group)
            self.stdout.write(self.style.SUCCESS(f'Removed role "{role}" from user "{username}".'))
        else:
            user.groups.add(group)
            self.stdout.write(self.style.SUCCESS(f'Assigned role "{role}" to user "{username}".'))
