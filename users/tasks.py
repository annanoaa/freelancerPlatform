from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .utils import generate_verification_token


@shared_task
def send_verification_email(user_id):
    from .models import User
    try:
        user = User.objects.get(id=user_id)
        token = generate_verification_token(user)

        # Explicit printing with clear markers
        print("\n")
        print("=" * 50)
        print("VERIFICATION TOKEN DETAILS")
        print("=" * 50)
        print(f"User ID: {user_id}")
        print(f"User Email: {user.email}")
        print(f"Token: {token}")
        print("=" * 50)
        print("\n")

        verification_url = f"{settings.SITE_URL}/verify-email/{token}"

        message = f"""
        Hello {user.first_name},

        Please verify your email address using this token: {token}

        Or click this link: {verification_url}

        Thanks for registering!
        """

        # Log before sending email
        print("Attempting to send email...")

        send_mail(
            'Verify your email address',
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )

        return token  # Return the token explicitly

    except User.DoesNotExist:
        print(f"ERROR: User with ID {user_id} not found!")
    except Exception as e:
        print(f"ERROR: {str(e)}")