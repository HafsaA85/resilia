from django.core.management.base import BaseCommand
from django.utils import timezone

from organisations.models import OrganisationLicense, OrganisationMembership


class Command(BaseCommand):
    help = "Deactivate users when organisation licence expires"

    def handle(self, *args, **kwargs):
        today = timezone.now().date()

        expired_licenses = OrganisationLicense.objects.filter(
            end_date__lt=today,
            status="active"
        )

        count_orgs = 0
        count_users = 0

        for lic in expired_licenses:
            lic.status = "expired"
            lic.save()

            users = OrganisationMembership.objects.filter(
                organisation=lic.organisation,
                is_active=True
            )

            deactivated = users.update(is_active=False)

            count_orgs += 1
            count_users += deactivated

        self.stdout.write(
            self.style.SUCCESS(
                f"Expired {count_orgs} licences and deactivated {count_users} users"
            )
        )