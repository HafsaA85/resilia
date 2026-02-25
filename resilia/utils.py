from .models import AnxietyTrigger, CBTExercise


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