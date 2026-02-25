from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from datetime import date

User = settings.AUTH_USER_MODEL


class Organisation(models.Model):
    name = models.CharField(max_length=255)
    domain = models.CharField(max_length=255, blank=True, null=True)
    contact_email = models.EmailField()
    contact_name = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class OrganisationMembership(models.Model):
    ROLE_OWNER = "owner"
    ROLE_ADMIN = "admin"
    ROLE_HR = "hr_manager"
    ROLE_MEMBER = "member"

    ROLE_CHOICES = [
        (ROLE_OWNER, "Owner"),
        (ROLE_ADMIN, "Admin"),
        (ROLE_HR, "HR Licence Manager"),
        (ROLE_MEMBER, "Member"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE)
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_MEMBER
    )
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "organisation")

    def __str__(self):
        return f"{self.user} @ {self.organisation}"


class OrganisationLicense(models.Model):
    PLAN_CHOICES = [
        ("starter", "Starter"),
        ("growth", "Growth"),
        ("scale", "Scale"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("expired", "Expired"),
        ("trial", "Trial"),
        ("suspended", "Suspended"),
    ]

    organisation = models.OneToOneField(
        Organisation,
        on_delete=models.CASCADE,
        related_name="license"
    )
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES)
    seats = models.PositiveIntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active"
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def clean(self):
        active_users = OrganisationMembership.objects.filter(
            organisation=self.organisation,
            is_active=True
        ).count()

        if self.seats < active_users:
            raise ValidationError(
                f"Seats ({self.seats}) cannot be less than active users ({active_users})."
            )

    def is_active(self):
        return self.status == "active" and self.end_date >= date.today()

    def __str__(self):
        return f"{self.organisation} ({self.plan})"


class Invoice(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("sent", "Sent"),
        ("paid", "Paid"),
        ("overdue", "Overdue"),
    ]

    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE)
    invoice_number = models.CharField(max_length=50, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    issue_date = models.DateField()
    due_date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft"
    )
    billing_period_start = models.DateField()
    billing_period_end = models.DateField()
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.invoice_number} - {self.organisation}"