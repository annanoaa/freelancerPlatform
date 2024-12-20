from urllib.parse import unquote

from django.conf import settings
from django.core.signing import TimestampSigner
from django.template.loader import render_to_string

def generate_verification_token(user):
    signer = TimestampSigner()
    return signer.sign(user.email)


def verify_token(token, max_age=86400):  # 24 hours
    try:
        # Decode URL-encoded token
        decoded_token = unquote(token)
        print(f"Attempting to verify token: {decoded_token}")  # Debug print

        signer = TimestampSigner()
        email = signer.unsign(decoded_token, max_age=max_age)
        print(f"Successfully decoded email: {email}")  # Debug print
        return email
    except Exception as e:
        print(f"Token verification failed: {str(e)}")  # Debug print
        return None