from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User, Group
from django.utils.crypto import get_random_string
import os


class Command(BaseCommand):
    help = 'Create default admin and verifier accounts for the application.'

    def add_arguments(self, parser):
        parser.add_argument('--admin-username', type=str, help='Admin username')
        parser.add_argument('--admin-email', type=str, help='Admin email address')
        parser.add_argument('--admin-password', type=str, help='Admin password')
        parser.add_argument('--verifier-username', type=str, help='Verifier username')
        parser.add_argument('--verifier-email', type=str, help='Verifier email address')
        parser.add_argument('--verifier-password', type=str, help='Verifier password')
        parser.add_argument('--force', action='store_true', help='Force update existing user roles and passwords')
        parser.add_argument('--auto', action='store_true', help='Use environment variables for account values')

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Creating default groups and accounts...'))

        self._ensure_group('client')
        self._ensure_group('verifier')
        self._ensure_group('admin')

        admin = self._get_account_data(
            options,
            'admin_username',
            'DEFAULT_ADMIN_USERNAME',
            'admin_password',
            'DEFAULT_ADMIN_PASSWORD',
            'admin_email',
            'DEFAULT_ADMIN_EMAIL',
        )

        verifier = self._get_account_data(
            options,
            'verifier_username',
            'DEFAULT_VERIFIER_USERNAME',
            'verifier_password',
            'DEFAULT_VERIFIER_PASSWORD',
            'verifier_email',
            'DEFAULT_VERIFIER_EMAIL',
        )

        if options['auto']:
            if admin['username']:
                self._create_or_update_admin(admin, options['force'])
            else:
                self.stdout.write(self.style.WARNING('Skipping admin creation: DEFAULT_ADMIN_USERNAME not set.'))

            if verifier['username']:
                self._create_or_update_verifier(verifier, options['force'])
            else:
                self.stdout.write(self.style.WARNING('Skipping verifier creation: DEFAULT_VERIFIER_USERNAME not set.'))
        else:
            if not admin['username'] and not verifier['username']:
                raise CommandError('No account data supplied. Use command arguments or --auto with environment variables.')
            if admin['username']:
                self._create_or_update_admin(admin, options['force'])
            if verifier['username']:
                self._create_or_update_verifier(verifier, options['force'])

        self.stdout.write(self.style.SUCCESS('Default account creation complete.'))

    def _ensure_group(self, name):
        group, created = Group.objects.get_or_create(name=name)
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created group: {name}'))
        return group

    def _get_account_data(self, options, username_key, username_env, password_key, password_env, email_key, email_env):
        return {
            'username': options.get(username_key) or os.getenv(username_env),
            'password': options.get(password_key) or os.getenv(password_env),
            'email': options.get(email_key) or os.getenv(email_env),
        }

    def _create_or_update_admin(self, data, force):
        if not data['username']:
            return

        user, created = User.objects.get_or_create(username=data['username'])
        user.email = data['email'] or user.email
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True

        if created:
            if not data['password']:
                raise CommandError('Admin password is required for a new admin account.')
            user.set_password(data['password'])
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Created admin user: {data["username"]}'))
        else:
            if force:
                if data['password']:
                    user.set_password(data['password'])
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Updated admin user: {data["username"]}'))
            else:
                self.stdout.write(self.style.NOTICE(f'Admin user already exists: {data["username"]}'))

        admin_group = self._ensure_group('admin')
        user.groups.add(admin_group)

    def _create_or_update_verifier(self, data, force):
        if not data['username']:
            return

        user, created = User.objects.get_or_create(username=data['username'])
        user.email = data['email'] or user.email
        user.is_active = True
        user.is_staff = False
        user.is_superuser = False

        if created:
            if not data['password']:
                raise CommandError('Verifier password is required for a new verifier account.')
            user.set_password(data['password'])
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Created verifier user: {data["username"]}'))
        else:
            if force:
                if data['password']:
                    user.set_password(data['password'])
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Updated verifier user: {data["username"]}'))
            else:
                self.stdout.write(self.style.NOTICE(f'Verifier user already exists: {data["username"]}'))

        verifier_group = self._ensure_group('verifier')
        user.groups.add(verifier_group)
