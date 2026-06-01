from urllib import response

import requests
from django.conf import settings


def send_verification_email(user, verification_link):

    url = "https://api.brevo.com/v3/smtp/email"

    headers = {
        "accept": "application/json",
        "api-key": settings.BREVO_API_KEY,
        "content-type": "application/json"
    }

    data = {
        "sender": {
            "name": settings.BREVO_SENDER_NAME,
            "email": settings.BREVO_SENDER_EMAIL
        },
        "to": [
            {
                "email": user.email,
                "name": user.first_name
            }
        ],
        "subject": "Verify your Veylin account",
        "htmlContent": f"""
        <html>
            <body>
                <h2>Welcome to Veylin</h2>

                <p>Please verify your email address.</p>

                <a href="{verification_link}">
                    Verify My Account
                </a>
            </body>
        </html>
        """
    }

    response = requests.post(url, json=data, headers=headers)


    return response.json()

def add_user_to_brevo(user):

    url = "https://api.brevo.com/v3/contacts"

    headers = {
        "accept": "application/json",
        "api-key": settings.BREVO_API_KEY,
        "content-type": "application/json"
    }

    data = {
        "email": user.email,
        "attributes": {
            "FIRSTNAME": user.first_name,
            "LASTNAME": user.last_name,
        },
        "listIds": [7],
        "updateEnabled": True
    }

    response = requests.post(url, json=data, headers=headers)

    print("BREVO STATUS:", response.status_code)
    print("BREVO RESPONSE:", response.text)

    return response.text