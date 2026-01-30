from django.contrib import admin
from .models import AnxietyTrigger, JournalEntry, DailyPrompt


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

