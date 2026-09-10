# shop/utils.py
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
import os
from email.message import MIMEPart
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.models import User

from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings


def send_order_confirmation(uidb64, user_email, user_username, verify_token,):

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


def trigger_mail_verification(user_id, verify_token):
    user = User.objects.get(pk=user_id)
    user_bytes = force_bytes(user.id)
    uidb64 = urlsafe_base64_encode(user_bytes)
    send_order_confirmation(uidb64, user.email, user.username, verify_token)