from django.contrib import admin
from .models import AnxietyTrigger, CBTExercise, JournalEntry, DailyPrompt
from .models import OrganisationLead
import csv
from django.http import HttpResponse
from .models import CBTExercise


@admin.register(AnxietyTrigger)
class AnxietyTriggerAdmin(admin.ModelAdmin):
    list_display = ("user", "situation", "intensity", "created_at")
    list_filter = ("intensity", "created_at")
    search_fields = ("situation", "user__username")
    ordering = ("-created_at",)


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at", "trigger")
    list_filter = ("created_at",)
    search_fields = ("content", "user__username")
    ordering = ("-created_at",)


@admin.register(DailyPrompt)
class DailyPromptAdmin(admin.ModelAdmin):
    list_display = ("text", "theme", "active")
    list_filter = ("theme", "active")
    search_fields = ("text",)


@admin.register(OrganisationLead)
class OrganisationLeadAdmin(admin.ModelAdmin):
    list_display = (
        "organisation_name",
        "contact_name",
        "email",
        "organisation_type",
        "organisation_size",
        "city",
        "country",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "organisation_type",
        "city",
        "created_at",
    )

    search_fields = (
        "organisation_name",
        "contact_name",
        "email",
    )

    ordering = ("-created_at",)
    readonly_fields = ("created_at",)

    fieldsets = (
        ("Organisation", {
            "fields": (
                "organisation_name",
                "organisation_type",
                "organisation_size",
                "city",
                "country",
            )
        }),
        ("Contact", {
            "fields": (
                "contact_name",
                "email",
                "role",
            )
        }),
        ("Enquiry", {
            "fields": (
                "message",
                "notes",
                "status",
            )
        }),
        ("Meta", {
            "fields": ("created_at",),
        }),
    )

    actions = [
        "export_csv",
        "mark_contacted",
        "mark_demo",
        "mark_converted",
    ]

    # ---------- CSV EXPORT ----------
    def export_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=resilia_leads.csv"

        writer = csv.writer(response)
        writer.writerow([
            "Organisation",
            "Contact",
            "Email",
            "Type",
            "Size",
            "Status",
            "Created",
        ])

        for lead in queryset:
            writer.writerow([
                lead.organisation_name,
                lead.contact_name,
                lead.email,
                lead.organisation_type,
                lead.organisation_size,
                lead.status,
                lead.created_at,
            ])

        return response

    export_csv.short_description = "Export selected leads to CSV"

    # ---------- PIPELINE ACTIONS ----------
    def mark_contacted(self, request, queryset):
        queryset.update(status="contacted")

    mark_contacted.short_description = "Mark as Contacted"

    def mark_demo(self, request, queryset):
        queryset.update(status="demo")

    mark_demo.short_description = "Mark as Demo Scheduled"

    def mark_converted(self, request, queryset):
        queryset.update(status="converted")

    mark_converted.short_description = "Mark as Converted"

    @admin.register(CBTExercise)
    
    class CBTExerciseAdmin(admin.ModelAdmin):
        list_display = ("title", "mood_level")
        list_filter = ("mood_level",)
search_fields = ("title", "description")