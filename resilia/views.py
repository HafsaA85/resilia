from urllib import request

from django.http import JsonResponse
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
from .models import AnxietyTrigger, JournalEntry, Subscription, OrganisationLead, CBTExercise
from .forms import AnxietyTriggerForm, JournalEntryForm, OrganisationContactForm
from django.core.mail import send_mail
from .utils import get_user_cbt_recommendations
from django.views.decorators.csrf import csrf_exempt
import stripe
import json
from .forms import UserRegisterForm
import json
from django.conf import settings
from django.http import JsonResponse, HttpResponse

stripe.api_key = settings.STRIPE_SECRET_KEY


# =========================
# SUBMIT LEAD
# =========================
@csrf_exempt
def submit_lead(request):
    if request.method == "POST":
        data = json.loads(request.body)

        OrganisationLead.objects.create(
            organisation_name=data.get("organisation_name"),
            contact_name=data.get("contact_name"),
            phone=data.get("phone"),
            email=data.get("email"),
            role=data.get("role"),
            organisation_type=data.get("organisation_type"),
            organisation_size=data.get("organisation_size"),
            message=data.get("message"),
        )

        return JsonResponse({"success": True})

    return JsonResponse({"success": False})


def premium_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated:
            return redirect("resilia:login")

        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        try:
            sub = Subscription.objects.get(user=request.user)
        except Subscription.DoesNotExist:
            return redirect("resilia:upgrade")

        if not sub.is_active:
         return redirect("resilia:upgrade")

        if sub.is_active:
          return view_func(request, *args, **kwargs)
        

        return redirect("resilia:upgrade")
    return wrapper
    
    
# =========================
# CONTACT
# =========================
def contact(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        message = request.POST.get("message")

        OrganisationLead.objects.create(
            contact_name=name,
            email=email,
            phone=phone,
            message=message,
        )

        send_mail(
            subject="New Coaching Request",
            message=f"""
New coaching request received:

Name: {name}
Email: {email}
Phone: {phone}

Message:
{message}
""",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.DEFAULT_FROM_EMAIL],
        )

        return redirect("resilia:contact_success")

    return render(request, "contact.html")


def contact_success(request):
    return render(request, "contact_success.html")


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

    # ✅ SIMPLE ACCESS (NO STRIPE CALLS)
    has_access = True
    trial_days_left = None
    show_upgrade_prompt = False

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
            "trial_days_left": trial_days_left,
            "show_upgrade_prompt": show_upgrade_prompt,
            "has_access": has_access,
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
        form = UserRegisterForm(request.POST)  
        if form.is_valid():
            user = form.save(commit=False)
            user.first_name = form.cleaned_data.get('first_name')
            user.last_name = form.cleaned_data.get('last_name')
            user.save()
            Subscription.objects.create(user=user)
            login(request, user)
            return redirect("resilia:home")
    else:
        form = UserRegisterForm()

    return render(request, "register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            
            return redirect("resilia:home")

        messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, "login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("resilia:home")


# =========================
# TRACKER
# =========================
@login_required
@premium_required
def tracker_list(request):
    triggers = AnxietyTrigger.objects.filter(user=request.user)
    exercises = get_user_cbt_recommendations(request.user)

    return render(
        request,
        "tracker_list.html",
        {
            "triggers": triggers,
            "exercises": exercises,
        },
    )


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
                    "That sounds really intense. You don’t have to solve anything right now. Just breathe."
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

@login_required
@premium_required
def exercise_detail(request, pk):
    exercise = get_object_or_404(CBTExercise, pk=pk)
    return render(request, "exercise_detail.html", {"exercise": exercise})

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

    return render(request, "journal/form.html", {
        "form": form,
        "edit": True
    })

@login_required
@premium_required
def journal_delete(request, pk):
    entry = get_object_or_404(JournalEntry, pk=pk, user=request.user)

    if request.method == "POST":
        entry.delete()
        return redirect("resilia:journal_list")

    return render(request, "journal/confirm_delete.html", {
        "entry": entry
    })

@login_required
def customer_portal(request):
    try:
        sub = Subscription.objects.get(user=request.user)
    except Subscription.DoesNotExist:
        return redirect("resilia:upgrade")

    if sub.stripe_customer_id:
        domain_url = request.build_absolute_uri("/")

        session = stripe.billing_portal.Session.create(
            customer=sub.stripe_customer_id,
            return_url=domain_url,
        )

        return redirect(session.url)

    return redirect("resilia:checkout")
    
# =========================
# STRIPE
# =========================
@login_required
def create_checkout_session(request):
    domain_url = request.build_absolute_uri('/')

    if not request.user.email:
        messages.error(request, "Please add an email to continue.")
        return redirect("resilia:home")

    session = stripe.checkout.Session.create(
    payment_method_types=["card"],
    mode="subscription",
    customer_email=request.user.email,
    billing_address_collection='required',
    allow_promotion_codes=True,
    line_items=[{
        "price": "price_1Szn42FT8cf21M5WpK8rHELs",
        "quantity": 1,
    }],
    subscription_data={"trial_period_days": 7},
    success_url=domain_url + "success/?session_id={CHECKOUT_SESSION_ID}",
    cancel_url=domain_url + "upgrade/",
    metadata={
        "user_id": request.user.id
    }
)

    return redirect(session.url)

 



def upgrade(request):
    has_used_trial = False  # default

    if request.user.is_authenticated:
        try:
            sub = Subscription.objects.get(user=request.user)
            has_used_trial = sub.has_used_trial
        except Subscription.DoesNotExist:
            has_used_trial = False

    return render(request, "upgrade.html", {
        "has_used_trial": has_used_trial
    })
    

def subscription_success(request):
    session_id = request.GET.get("session_id")

    if not session_id:
        return redirect("resilia:home")

    try:
        session = stripe.checkout.Session.retrieve(session_id)

        sub, _ = Subscription.objects.get_or_create(user=request.user)
        sub.is_active = True
        sub.stripe_customer_id = session.get("customer")
        sub.save()

        messages.success(request, "Your subscription is now active 🎉")

    except Exception as e:
        print("Stripe error:", e)
        messages.error(request, "Something went wrong.")

    return render(request, "subscription_success.html")



def subscription_cancel(request):
    return render(request, "subscription_cancel.html")

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except Exception:
        return HttpResponse(status=400)

    event_type = event["type"]
    data = event["data"]["object"]

    print("Stripe event:", event_type)

    # ✅ When checkout completes
    if event_type == "checkout.session.completed":
        user_id = data["metadata"].get("user_id")
        customer_id = data["customer"]
        subscription_id = data.get("subscription")

        # ✅ Get name + email from Stripe
        customer_details = data.get("customer_details", {})
        name = customer_details.get("name")
        email = customer_details.get("email")

        print("Name:", name)
        print("Email:", email)

        # ✅ Get user from DB first
        sub = Subscription.objects.get(user_id=user_id)
        user = sub.user

        # ✅ Use Django name (correct source)
        full_name = f"{user.first_name} {user.last_name}"

        # ✅ Update Stripe with correct name
        stripe.Customer.modify(
            customer_id,
            name=full_name,
            email=user.email
        )

        # ✅ Split name
        first_name = ""
        last_name = ""

        if name:
            parts = name.split(" ", 1)
            first_name = parts[0]
            if len(parts) > 1:
                last_name = parts[1]

        try:
            sub = Subscription.objects.get(user_id=user_id)

            # ✅ Update subscription
            sub.stripe_customer_id = customer_id
            sub.stripe_subscription_id = subscription_id
            sub.is_active = True
            sub.has_used_trial = False
            sub.save()

            print("✅ Webhook updated subscription + user:", user_id)

        except Exception as e:
            print("❌ Webhook error:", e)

    return HttpResponse(status=200)