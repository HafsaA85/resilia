from openai import OpenAI
from django.conf import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)


def generate_outreach_email(lead):

    prompt = f"""
    Write a short professional outreach email.

    Organisation: {lead.organisation_name}
    Contact: {lead.contact_name}
    Role: {lead.role}
    Organisation Type: {lead.organisation_type}

    The email should introduce Resilia, which provides
    resilience training and workshops for schools and organisations.

    Keep it short and friendly.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content