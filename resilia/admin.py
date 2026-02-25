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
        "status",
        "created_at",
    )

    list_filter = ("status", "organisation_type", "created_at")
    search_fields = ("organisation_name", "contact_name", "email")
    ordering = ("-created_at",)

    actions = ["export_csv"]

    def export_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=resilia_leads.csv"

        writer = csv.writer(response)
        writer.writerow([
            "Organisation",
            "Contact",
            "Email",
            "Type",
            "Status",
            "Created",
        ])

        for lead in queryset:
            writer.writerow([
                lead.organisation_name,
                lead.contact_name,
                lead.email,
                lead.organisation_type,
                lead.status,
                lead.created_at,
            ])

        return response

    export_csv.short_description = "Export selected leads to CSV"

    @admin.register(CBTExercise)
    
    class CBTExerciseAdmin(admin.ModelAdmin):
        list_display = ("title", "mood_level")
        list_filter = ("mood_level",)
search_fields = ("title", "description")