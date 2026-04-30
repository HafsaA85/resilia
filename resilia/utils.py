from .models import AnxietyTrigger, CBTExercise
from django.utils import timezone
from datetime import timedelta


def should_show_support_banner(request):
    time_str = request.session.get("support_banner_time")

    if not time_str:
        return False

    try:
        banner_time = timezone.datetime.fromisoformat(time_str)
    except Exception:
        return False

    return timezone.now() - banner_time < timedelta(hours=48)

def anxiety_to_band(intensity: int) -> str:
    """
    Convert anxiety intensity (1–10) to CBT band.
    """
    if intensity <= 3:
        return "low"
    elif intensity <= 6:
        return "moderate"
    elif intensity <= 8:
        return "high"
    else:
        return "overwhelmed"


def get_user_cbt_recommendations(user):
    """
    Return CBT exercises matched to user's latest anxiety trigger.
    """
    latest_trigger = (
        AnxietyTrigger.objects
        .filter(user=user)
        .order_by("-date", "-created_at")
        .first()
    )

    if not latest_trigger:
        return CBTExercise.objects.filter(mood_level="low")

    band = anxiety_to_band(latest_trigger.intensity)

    return CBTExercise.objects.filter(mood_level=band)