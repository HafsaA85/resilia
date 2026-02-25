from django.contrib import admin
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import Permission

from .models import Organisation, OrganisationMembership, OrganisationLicense, Invoice


# ---------- Helper ----------
def get_user_membership(user):
    return OrganisationMembership.objects.filter(user=user).first()


def user_org(user):
    m = get_user_membership(user)
    return m.organisation if m else None


# ---------- Expiry Filter ----------
class ExpirySoonFilter(admin.SimpleListFilter):
    title = "Expiry window"
    parameter_name = "expiry_window"

    def lookups(self, request, model_admin):
        return (
            ("30", "Next 30 days"),
            ("60", "Next 60 days"),
            ("90", "Next 90 days"),
        )

    def queryset(self, request, queryset):
        if self.value():
            days = int(self.value())
            today = timezone.now().date()
            future = today + timedelta(days=days)
            return queryset.filter(end_date__range=(today, future))
        return queryset


# ---------- Organisation ----------
@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    list_display = ("name", "contact_email", "created_at")
    search_fields = ("name", "contact_email")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        org = user_org(request.user)
        return qs.filter(id=org.id) if org else qs.none()


# ---------- Membership ----------
@admin.register(OrganisationMembership)
class OrganisationMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "organisation", "role", "is_active", "joined_at")
    list_filter = ("role", "organisation", "is_active")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        org = user_org(request.user)
        return qs.filter(organisation=org) if org else qs.none()

    def save_model(self, request, obj, form, change):
        user = obj.user

        # ---------- HR STAFF + PERMISSIONS ----------
        if obj.role == OrganisationMembership.ROLE_HR:
            if not user.is_staff:
                user.is_staff = True

            perms = Permission.objects.filter(
                content_type__app_label="organisations",
                codename__in=[
                    "view_organisation",
                    "view_organisationmembership",
                    "add_organisationmembership",
                    "change_organisationmembership",
                    "view_organisationlicense",
                    "view_invoice",
                ],
            )
            user.user_permissions.add(*perms)
            user.save()

        else:
            # Remove staff if no longer HR (and not superuser)
            if user.is_staff and not user.is_superuser:
                still_hr = OrganisationMembership.objects.filter(
                    user=user,
                    role=OrganisationMembership.ROLE_HR,
                    is_active=True
                ).exclude(pk=obj.pk).exists()

                if not still_hr:
                    user.is_staff = False
                    user.user_permissions.clear()
                    user.save()
        # -------------------------------------------

        # HR can only manage their org
        if not request.user.is_superuser:
            obj.organisation = user_org(request.user)

        # ---------- Seat enforcement ----------
        if obj.is_active:
            license = OrganisationLicense.objects.filter(
                organisation=obj.organisation,
                status="active"
            ).first()

            if license:
                active_count = OrganisationMembership.objects.filter(
                    organisation=obj.organisation,
                    is_active=True
                ).exclude(pk=obj.pk).count()

                if active_count >= license.seats:
                    raise ValidationError(
                        "Licence limit reached for this organisation."
                    )
        # --------------------------------------

        super().save_model(request, obj, form, change)


# ---------- License ----------
@admin.register(OrganisationLicense)
class OrganisationLicenseAdmin(admin.ModelAdmin):
    list_display = (
        "organisation",
        "plan",
        "seats",
        "active_users",
        "available_seats",
        "status",
        "end_date",
        "days_to_expiry",
        "expiry_status",
    )
    list_filter = ("plan", "status", ExpirySoonFilter)
    search_fields = ("organisation__name",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        org = user_org(request.user)
        return qs.filter(organisation=org) if org else qs.none()

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    # ----- Licence Usage -----
    def active_users(self, obj):
        return OrganisationMembership.objects.filter(
            organisation=obj.organisation,
            is_active=True
        ).count()

    def available_seats(self, obj):
        return max(obj.seats - self.active_users(obj), 0)

    active_users.short_description = "Active Users"
    available_seats.short_description = "Available Seats"

    # ----- Renewal Monitoring -----
    def days_to_expiry(self, obj):
        return (obj.end_date - timezone.now().date()).days

    def expiry_status(self, obj):
        days = (obj.end_date - timezone.now().date()).days

        if days < 0:
            return "🔴 Expired"
        elif days <= 30:
            return "🟠 <30d"
        elif days <= 60:
            return "🟡 <60d"
        else:
            return "🟢 Active"

    days_to_expiry.short_description = "Days Left"
    expiry_status.short_description = "Expiry"


# ---------- Invoice ----------
@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("invoice_number", "organisation", "amount", "status", "due_date")
    list_filter = ("status",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        org = user_org(request.user)
        return qs.filter(organisation=org) if org else qs.none()