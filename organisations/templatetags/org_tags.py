from django import template
from organisations.models import OrganisationMembership

register = template.Library()


@register.simple_tag
def has_organisation(user):
    if not user.is_authenticated:
        return False
    return OrganisationMembership.objects.filter(user=user, is_active=True).exists()