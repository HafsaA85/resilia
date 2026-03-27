from django.db import models
from django.contrib.auth.models import User


# =========================
# Subscription
# =========================
class Subscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=False)
    free_access = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} Subscription"


# =========================
# Anxiety Trigger (CBT core)
# =========================
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
        db_table = "noorforher_anxietytrigger"  # keep existing table

    def __str__(self):
        return f"{self.title} ({self.date})"


# =========================
# Journal Entry
# =========================
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

    class Meta:
        db_table = "noorforher_journalentry"  # keep existing table

    def __str__(self):
        return self.title


# =========================
# Daily Prompt
# =========================
class DailyPrompt(models.Model):
    PROMPT_THEMES = [
        ("journal", "Free Journal"),
        ("reflection", "Trigger Reflection"),
    ]

    text = models.CharField(max_length=300)
    theme = models.CharField(max_length=20, choices=PROMPT_THEMES, default="journal")
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "noorforher_dailyprompt"

    def __str__(self):
        return f"{self.theme}: {self.text}"


# =========================
# Organisation Lead (B2B sales)
# =========================
class OrganisationLead(models.Model):

    STATUS_CHOICES = [
        ("new", "New"),
        ("contacted", "Contacted"),
        ("demo", "Demo Scheduled"),
        ("converted", "Converted"),
        ("closed", "Closed"),
    ]

    organisation_name = models.CharField(max_length=150)
    contact_name = models.CharField(max_length=100)
    email = models.EmailField()

    role = models.CharField(max_length=100, blank=True)
    organisation_type = models.CharField(max_length=100, blank=True)
    organisation_size = models.CharField(max_length=50, blank=True)
    phase = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True, default="UK")

    message = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="new"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.organisation_name} — {self.contact_name}"


# =========================
# CBT Exercise Library
# =========================
class CBTExercise(models.Model):
    MOOD_CHOICES = [
        ("low", "Low anxiety"),
        ("moderate", "Moderate anxiety"),
        ("high", "High anxiety"),
        ("overwhelmed", "Overwhelmed"),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    instructions = models.TextField()
    mood_level = models.CharField(max_length=20, choices=MOOD_CHOICES)

    class Meta:
        db_table = "resilia_cbtexercise"

    def __str__(self):
        return self.title

# =========================
# Free Access Code
# =========================

class AccessCode(models.Model):
    code = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)
    max_uses = models.IntegerField(default=100)
    used_count = models.IntegerField(default=0)

    def __str__(self):
        return self.code