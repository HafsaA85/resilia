from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.db.models import Avg, Count
from django.conf import settings
from functools import wraps
from .models import AnxietyTrigger, JournalEntry, Subscription, OrganisationLead
from .forms import AnxietyTriggerForm, JournalEntryForm
import stripe
from .forms import OrganisationContactForm
from django.core.mail import send_mail
from django.conf import settings
from .utils import get_user_cbt_recommendations
from .models import CBTExercise

# =========================
# PREMIUM DECORATOR
# =========================
def premium_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated:
            return redirect("resilia:login")

        # allow admin access for testing
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        if not hasattr(request.user, "subscription") or not request.user.subscription.is_active:
            return redirect("resilia:upgrade")

        return view_func(request, *args, **kwargs)

    return wrapper

def contact(request):
    if request.method == "POST":
        form = OrganisationContactForm(request.POST)
        if form.is_valid():

            # ✅ Save lead
            OrganisationLead.objects.create(
                organisation_name=form.cleaned_data["organisation_name"],
                contact_name=form.cleaned_data["contact_name"],
                email=form.cleaned_data["email"],
                role=form.cleaned_data.get("role", ""),
                organisation_type=form.cleaned_data.get("organisation_type", ""),
                message=form.cleaned_data.get("message", ""),
            )

            # ✅ SEND EMAIL HERE
            send_mail(
                subject="New Resilia Organisation Enquiry",
                message=f"""
New organisation enquiry received:

Organisation: {form.cleaned_data['organisation_name']}
Contact: {form.cleaned_data['contact_name']}
Email: {form.cleaned_data['email']}
Type: {form.cleaned_data.get('organisation_type','')}
Message: {form.cleaned_data.get('message','')}
""",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.DEFAULT_FROM_EMAIL],
            )

            messages.success(request, "Thank you. We will contact you shortly.")
            return redirect("contact")

    else:
        form = OrganisationContactForm()

    return render(request, "contact.html", {"form": form})


stripe.api_key = settings.STRIPE_SECRET_KEY

print("✅ resilia.views loaded")


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

    coaching_message = None
    weekly_focus = None
    tiny_challenge = None
    reflection_prompt = None

    if triggers.exists():
        avg_intensity = triggers.aggregate(avg=Avg("intensity"))["avg"]
        high_intensity_count = triggers.filter(intensity__gte=7).count()

        insights = {
            "avg_intensity": round(avg_intensity, 1) if avg_intensity else 0,
            "high_intensity_count": high_intensity_count,
            "entries_last_7": triggers.filter(
                created_at__date__gte=today - timedelta(days=6)
            ).count(),
            "top_triggers": (
                triggers.values("situation")
                .annotate(count=Count("id"))
                .order_by("-count")[:3]
            ),
        }

        # -------- Digital Emotional Coach Logic --------
        if avg_intensity and avg_intensity >= 7:
            coaching_message = (
                "Your nervous system has been under pressure lately. "
                "This week is about slowing down."
            )
            weekly_focus = "Nervous System Regulation"
            tiny_challenge = "Take 3 slow breaths before responding to stress."
            reflection_prompt = "What makes it difficult for you to pause?"

        elif high_intensity_count >= 3:
            coaching_message = (
                "You've experienced several high-intensity moments. "
                "A pattern may be forming."
            )
            weekly_focus = "Pattern Awareness"
            tiny_challenge = "Notice when anxiety rises and name the trigger."
            reflection_prompt = "What situations repeat most often?"

        else:
            coaching_message = (
                "You are building awareness. Small reflections create powerful change."
            )
            weekly_focus = "Gentle Growth"
            tiny_challenge = "Journal once this week without judging your thoughts."
            reflection_prompt = "What are you proud of handling recently?"

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
            "coaching_message": coaching_message,
            "weekly_focus": weekly_focus,
            "tiny_challenge": tiny_challenge,
            "reflection_prompt": reflection_prompt,
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
            return redirect("resilia:home")
    else:
        form = UserCreationForm()

    return render(request, "register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("resilia:home")

        messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, "login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("resilia:home")


# =========================
# ANXIETY TRIGGERS
# =========================
@login_required
@premium_required
def tracker_list(request):
    
    triggers = AnxietyTrigger.objects.filter(user=request.user)
    return render(request, "tracker_list.html", {"triggers": triggers})


@login_required
@premium_required
def tracker_create(request):
    if request.method == "POST":
        form = AnxietyTriggerForm(request.POST)
        if form.is_valid():
            trigger = form.save(commit=False)
            trigger.user = request.user
            trigger.save()

            if trigger.intensity >= 8:
             messages.info(
        request,
        "That sounds really intense. "
        "You don’t have to solve anything right now. "
        "Just come back to your breath. "
        "One inhale. One exhale. "
        "You are safe in this moment."
    )


            return redirect("resilia:tracker_list")
    else:
        form = AnxietyTriggerForm()

    return render(request, "tracker_form.html", {"form": form})


@login_required
@premium_required
def tracker_update(request, pk):
    trigger = get_object_or_404(AnxietyTrigger, pk=pk, user=request.user)

    if request.method == "POST":
        form = AnxietyTriggerForm(request.POST, instance=trigger)
        if form.is_valid():
            form.save()
            return redirect("resilia:tracker_list")
    else:
        form = AnxietyTriggerForm(instance=trigger)

    return render(request, "tracker_form.html", {"form": form, "update": True})


# =========================
# JOURNAL
# =========================
@login_required
@premium_required
def journal_list(request):
    entries = JournalEntry.objects.filter(user=request.user)
    return render(request, "journal/list.html", {"entries": entries})


@login_required
@premium_required
def journal_create(request, trigger_id=None):
    trigger = None
    if trigger_id:
        trigger = get_object_or_404(
            AnxietyTrigger, pk=trigger_id, user=request.user
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
            return redirect("resilia:journal_list")
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
        {"form": form, "trigger": trigger},
    )


@login_required
@premium_required
def journal_edit(request, pk):
    entry = get_object_or_404(JournalEntry, pk=pk, user=request.user)

    if request.method == "POST":
        form = JournalEntryForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            return redirect("resilia:journal_list")
    else:
        form = JournalEntryForm(instance=entry)

    return render(request, "journal/form.html", {"form": form, "edit": True})


@login_required
@premium_required
def journal_delete(request, pk):
    entry = get_object_or_404(JournalEntry, pk=pk, user=request.user)

    if request.method == "POST":
        entry.delete()
        return redirect("resilia:journal_list")

    return render(request, "journal/confirm_delete.html", {"entry": entry})


# =========================
# STRIPE CUSTOMER PORTAL
# =========================
@login_required
def customer_portal(request):
    try:
        subscription = Subscription.objects.get(user=request.user)
    except Subscription.DoesNotExist:
        return redirect("resilia:upgrade")

    session = stripe.billing_portal.Session.create(
        customer=subscription.stripe_customer_id,
        return_url="http://127.0.0.1:8000/",
    )

    return redirect(session.url)



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
    exercises = get_user_cbt_recommendations(request.user)

    return render(
        request,
        "tracker_list.html",   # ✅ removed resilia/
        {
            "triggers": triggers,
            "exercises": exercises,
        },
    )

@login_required
@premium_required
def exercise_detail(request, pk):
    exercise = get_object_or_404(CBTExercise, pk=pk)
    return render(request, "exercise_detail.html", {"exercise": exercise})

@login_required
def create_checkout_session(request):
    import stripe
    from django.conf import settings

    stripe.api_key = settings.STRIPE_SECRET_KEY

    session = stripe.checkout.Session.create(
        mode="subscription",
        payment_method_types=["card"],
        line_items=[{
            "price": "prod_U3hcQS6mJSQCBH",  # replace with your TEST price
            "quantity": 1,
        }],
        success_url="http://127.0.0.1:8000/subscription-success/",
        cancel_url="http://127.0.0.1:8000/upgrade/",
    )

    return redirect(session.url)

stripe.api_key = settings.STRIPE_SECRET_KEY


@login_required
def create_checkout_session(request):
    email = request.user.email or "customer@example.com"

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="subscription",
        customer_email=email,
        line_items=[{
            "price": "price_1T5aD3FT8cf21M5WNz1g1INe",  # from Stripe
            "quantity": 1,
        }],
        success_url="http://127.0.0.1:8000/success/",
        cancel_url="http://127.0.0.1:8000/upgrade/",
    )

    return redirect(session.url)