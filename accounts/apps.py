from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = 'accounts'
    verbose_name = 'Accounts'

    def ready(self):
        # Create default groups for role-based access if they don't exist.
        try:
            from django.contrib.auth.models import Group
            Group.objects.get_or_create(name='client')
            Group.objects.get_or_create(name='verifier')
        except Exception:
            # avoid crashing during migrations or when auth isn't ready
            pass
