import csv
import os

from django.core.management.base import BaseCommand
from django.conf import settings
from resilia.models import OrganisationLead


class Command(BaseCommand):

    help = "Import independent schools from CSV"

    def handle(self, *args, **kwargs):

        file_path = os.path.join(settings.BASE_DIR, "resilia_project", "data", "schools.csv")

        count = 0

        with open(file_path, newline='', encoding="latin-1") as csvfile:

            reader = csv.DictReader(csvfile)

            for row in reader:
                school_type = row["TypeOfEstablishment (name)"]

                if school_type and "independent" in school_type.lower():

                    OrganisationLead.objects.get_or_create(
                        organisation_name=row["EstablishmentName"],
                        organisation_type="Independent School",
                        city=row["Town"],
                        country="UK",
                        phase=row.get("PhaseOfEducation (name)"), 
                        email="unknown@school.co.uk",
                        
                    )

                    count += 1

        self.stdout.write(self.style.SUCCESS(f"Imported {count} schools"))