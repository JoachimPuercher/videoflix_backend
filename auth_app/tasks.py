"""Mail jobs for account activation and password reset.

The trigger_* functions are enqueued with django-rq and run in the worker;
they receive plain values (id or address) and load the user themselves. The
send_* functions build the multipart mail with the inline logo and send it.
"""

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
import os
from email.message import MIMEPart
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.models import User

from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings


def send_password_reset_mail(uidb64, user_email, verify_token):
    """Send the reset mail; the link points to the frontend confirm page."""
    FRONTEND_URL=os.getenv('FRONTEND_URL')
    context = {
        "frontend_url" : f"{FRONTEND_URL}/pages/auth/login.html",
        "password_reset_link": f"{FRONTEND_URL}/pages/auth/confirm_password.html?uid={uidb64}&token={verify_token}",
    }
    text_body = render_to_string("reset_password.txt", context)
    html_body = render_to_string("reset_password.html", context)

    msg = EmailMultiAlternatives(
        subject="Reset password",
        body=text_body,
        from_email=None,                      
        to=[user_email],
    )
    
    msg.attach_alternative(html_body, "text/html")
    logo_path = settings.BASE_DIR / "auth_app" / "static" / "auth_app" / "logo.png"

    with open(logo_path, "rb") as f:
        logo_bytes = f.read()

    logo = MIMEPart()
    logo.set_content(
        logo_bytes,
        maintype="image",
        subtype="png",
        disposition="inline",
        filename="logo.png",
        cid="<videoflix_logo>",
    )
    msg.attach(logo)
    msg.send()


def send_order_confirmation(uidb64, user_email, user_username, verify_token,):
    """Send the activation mail; the link points straight to the API."""
    BACKEND_URL=os.getenv('BACKEND_URL')
    FRONTEND_URL=os.getenv('FRONTEND_URL')
    context = {
        "frontend_url": f"{FRONTEND_URL}/pages/auth/login.html",
        "user_name": user_username,
        "tracking_link": f"{BACKEND_URL}/api/activate/{uidb64}/{verify_token}/",
    }
    text_body = render_to_string("confirm_email.txt", context)
    html_body = render_to_string("confirm_email.html", context)

    msg = EmailMultiAlternatives(
        subject="Verify your account",
        body=text_body,
        from_email=None,                      
        to=[user_email],
    )
    
    msg.attach_alternative(html_body, "text/html")

    logo_path = settings.BASE_DIR / "auth_app" / "static" / "auth_app" / "logo.png"

    with open(logo_path, "rb") as f:
        logo_bytes = f.read()

    logo = MIMEPart()
    logo.set_content(
        logo_bytes,
        maintype="image",
        subtype="png",
        disposition="inline",
        filename="logo.png",
        cid="<videoflix_logo>",
    )
    msg.attach(logo)
    msg.send()


def trigger_password_reset(user_mail):
    """rq job: build uid and token for the address and send the reset mail."""
    user = User.objects.filter(email=user_mail).first()
    if user is None:
        # Unknown address: nothing to send, and no failed job in the registry.
        return
    verify_token = default_token_generator.make_token(user)
    user_bytes = force_bytes(user.id)
    uidb64 = urlsafe_base64_encode(user_bytes)
    send_password_reset_mail(uidb64, user.email, verify_token)

def trigger_mail_verification(user_id, verify_token):
    """rq job: send the activation mail for a freshly registered user."""
    user = User.objects.get(pk=user_id)
    user_bytes = force_bytes(user.id)
    uidb64 = urlsafe_base64_encode(user_bytes)
    send_order_confirmation(uidb64, user.email, user.username, verify_token)