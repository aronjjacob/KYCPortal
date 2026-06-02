from django.core.management.base import BaseCommand
from kyc.models import AdminDashboardFeature


class Command(BaseCommand):
    help = 'Seed the admin dashboard with initial features'

    def handle(self, *args, **options):
        features = [
            {
                'title': 'Manage Users',
                'description': 'Create, edit, and delete user accounts',
                'url_name': 'user_management',
                'icon': 'verified_user',
                'order': 1,
            },
            {
                'title': 'Review Documents',
                'description': 'Verify submitted KYC documents',
                'url_name': 'document_review',
                'icon': 'description',
                'order': 2,
            },
            {
                'title': 'Analytics',
                'description': 'View detailed reports and statistics',
                'url_name': 'admin_dashboard',
                'icon': 'analytics',
                'order': 3,
            },
        ]

        for feature_data in features:
            feature, created = AdminDashboardFeature.objects.get_or_create(
                url_name=feature_data['url_name'],
                defaults=feature_data
            )
            status = 'Created' if created else 'Already exists'
            self.stdout.write(
                self.style.SUCCESS(f'{status}: {feature.title}')
            )

        self.stdout.write(
            self.style.SUCCESS('Successfully seeded dashboard features!')
        )
