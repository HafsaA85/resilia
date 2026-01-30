from django.db import models
from django.contrib.auth.models import User


class AnxietyTrigger(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="triggers")
    title = models.CharField(max_length=200)
    situation = models.TextField(help_text="What happened? Where were you?")
    thoughts = models.TextField(blank=True, help_text="What thoughts came to your mind?")
    feelings = models.TextField(blank=True, help_text="How did you feel in your body?")
    intensity = models.IntegerField(help_text="Rate anxiety 1–10")
    behaviour = models.TextField(blank=True, help_text="What did you do or avoid?")
    outcome = models.TextField(blank=True, help_text="What was the result or consequence?")
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.title} ({self.date})"


class JournalEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="journal_entries")

    trigger = models.ForeignKey(
        AnxietyTrigger,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="journal_entries"
    )

    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class DailyPrompt(models.Model):
    PROMPT_THEMES = [
        ("journal", "Free Journal"),
        ("reflection", "Trigger Reflection"),
    ]

    text = models.CharField(max_length=300)
    theme = models.CharField(
        max_length=20,
        choices=PROMPT_THEMES,
        default="journal",
    )
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.text

    text = models.CharField(max_length=300)
    theme = models.CharField(max_length=20, choices=PROMPT_THEMES)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.theme}: {self.text}"

    created_at = models.DateTimeField(auto_now_add=True)