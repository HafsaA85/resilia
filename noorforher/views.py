from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.db.models import Avg, Count
from django.conf import settings
from django.http import JsonResponse
from functools import wraps
from .models import AnxietyTrigger, JournalEntry, Subscription
from .forms import AnxietyTriggerForm, JournalEntryForm
import stripe


stripe.api_key = settings.STRIPE_SECRET_KEY

print("✅ noorforher.views loaded")


# =========================
# HOME
# =========================
def home(request):
    if not request.user.is_authenticated:
        return render(request, "home.html")

    triggers = AnxietyTrigger.objects.filter(user=request.user)
    journal_entries = JournalEntry.objects.filter(user=request.user)

    today = timezone.now().date()
    last_7_days = [today - timedelta(days=i) for i in range(6, -1, -1)]

    journal_days = set(
        journal_entries.values_list("created_at__date", flat=True)
    )

    streak = 0
    for day in reversed(last_7_days):
        if day in journal_days:
            streak += 1
        else:
            break

    insights = None
    trend = None

    if triggers.exists():
        avg_intensity = triggers.aggregate(avg=Avg("intensity"))["avg"]

        insights = {
            "avg_intensity": round(avg_intensity, 1) if avg_intensity else 0,
            "high_intensity_count": triggers.filter(intensity__gte=7).count(),
            "entries_last_7": triggers.filter(
                created_at__date__gte=today - timedelta(days=6)
            ).count(),
            "top_triggers": (
                triggers.values("situation")
                .annotate(count=Count("id"))
                .order_by("-count")[:3]
            ),
        }

    affirmation = (
        "You are allowed to go gently. Healing does not rush."
        if journal_entries.exists()
        else None
    )

    return render(
        request,
        "home.html",
        {
            "last_7_days": last_7_days,
            "journal_days": journal_days,
            "streak": streak,
            "affirmation": affirmation,
            "insights": insights,
            "trend": trend,
        },
    )


# =========================
# STATIC PAGES
# =========================
def about(request):
    return render(request, "about.html")


def work_with_me(request):
    return render(request, "work_with_me.html")


def terms_of_use(request):
    return render(request, "terms_of_use.html")


def privacy_policy(request):
    return render(request, "privacy_policy.html")


# =========================
# AUTH
# =========================
def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("noorforher:home")
    else:
        form = UserCreationForm()

    return render(request, "register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("noorforher:home")

        messages.error(
            request,
            "Invalid username or password. Please try again."
        )
    else:
        form = AuthenticationForm()

    return render(request, "registration/login.html", {"form": form})

def logout_view(request):
    logout(request)
    return redirect("noorforher:home")


# =========================
# ANXIETY TRIGGERS
# =========================
@login_required
def tracker_list(request):
    triggers = AnxietyTrigger.objects.filter(user=request.user)
    return render(request, "tracker_list.html", {"triggers": triggers})


@login_required
def tracker_create(request):
    if request.method == "POST":
        form = AnxietyTriggerForm(request.POST)
        if form.is_valid():
            trigger = form.save(commit=False)
            trigger.user = request.user
            trigger.save()
            return redirect("noorforher:tracker_list")
    else:
        form = AnxietyTriggerForm()

    return render(request, "tracker_form.html", {"form": form})


@login_required
def tracker_update(request, pk):
    trigger = get_object_or_404(AnxietyTrigger, pk=pk, user=request.user)

    if request.method == "POST":
        form = AnxietyTriggerForm(request.POST, instance=trigger)
        if form.is_valid():
            form.save()
            return redirect("noorforher:tracker_list")
    else:
        form = AnxietyTriggerForm(instance=trigger)

    return render(request, "tracker_form.html", {"form": form, "update": True})


# =========================
# JOURNAL
# =========================
@login_required
def journal_list(request):
    entries = JournalEntry.objects.filter(user=request.user)
    return render(request, "journal/list.html", {"entries": entries})


@login_required
def journal_create(request, trigger_id=None):
    trigger = None

    if trigger_id:
        trigger = get_object_or_404(
            AnxietyTrigger,
            pk=trigger_id,
            user=request.user
        )

    if request.method == "POST":
        form = JournalEntryForm(request.POST)
        form.fields["trigger"].queryset = AnxietyTrigger.objects.filter(
            user=request.user
        )

        if form.is_valid():
            entry = form.save(commit=False)
            entry.user = request.user
            if trigger:
                entry.trigger = trigger
            entry.save()
            return redirect("noorforher:journal_list")
    else:
        form = JournalEntryForm(
            initial={"trigger": trigger} if trigger else None
        )
        form.fields["trigger"].queryset = AnxietyTrigger.objects.filter(
            user=request.user
        )

    return render(
        request,
        "journal/form.html",
        {"form": form, "trigger": trigger}
    )

    trigger = None
    if trigger_id:
        trigger = get_object_or_404(
            AnxietyTrigger, pk=trigger_id, user=request.user
        )

    if request.method == "POST":
        form = JournalEntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.user = request.user
            entry.trigger = trigger
            entry.save()
            return redirect("noorforher:journal_list")
    else:
        form = JournalEntryForm(initial={"trigger": trigger})

    return render(request, "journal/form.html", {"form": form})


@login_required
def journal_edit(request, pk):
    entry = get_object_or_404(JournalEntry, pk=pk, user=request.user)

    if request.method == "POST":
        form = JournalEntryForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            return redirect("noorforher:journal_list")
    else:
        form = JournalEntryForm(instance=entry)

    return render(request, "journal/form.html", {"form": form, "edit": True})


@login_required
def journal_delete(request, pk):
    entry = get_object_or_404(JournalEntry, pk=pk, user=request.user)

    if request.method == "POST":
        entry.delete()
        return redirect("noorforher:journal_list")

    return render(request, "journal/confirm_delete.html", {"entry": entry})


# =========================
# STRIPE CUSTOMER PORTAL
# =========================
@login_required
def customer_portal(request):
    try:
        subscription = Subscription.objects.get(user=request.user)
    except Subscription.DoesNotExist:
        return redirect("noorforher:upgrade")

    session = stripe.billing_portal.Session.create(
        customer=subscription.stripe_customer_id,
        return_url="http://127.0.0.1:8000/",
    )

    return redirect(session.url)


# =========================
# PREMIUM DECORATOR
# =========================
def premium_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("noorforher:login")

        if not hasattr(request.user, "subscription") or not request.user.subscription.is_active:
            return redirect("noorforher:upgrade")

        return view_func(request, *args, **kwargs)

    return wrapper


# =========================
# SUBSCRIPTION PAGES
# =========================
def upgrade(request):
    return render(request, "upgrade.html")


def subscription_success(request):
    return render(request, "subscription_success.html")


def subscription_cancel(request):
    return render(request, "subscription_cancel.html")

@login_required
@premium_required
def tracker_list(request):
    triggers = AnxietyTrigger.objects.filter(user=request.user)
    return render(request, "tracker_list.html", {"triggers": triggers})
