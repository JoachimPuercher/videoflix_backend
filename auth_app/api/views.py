"""Views of the auth API.

All endpoints here are public (no cookie needed): registration, activation,
login, logout, token refresh and password reset. Tokens travel only as
HttpOnly cookies; mails are sent through rq jobs.
"""

from rest_framework import generics, status, views
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .serializers import RegisterSerializer, EmailTokenObtainPairSerializer, EmailSerializer, ResetPasswordSerializer
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.models import User
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenBlacklistView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
import os
from .throttling import (
    ActivationThrottle,
    LoginThrottle,
    LogoutThrottle,
    PasswordConfirmThrottle,
    PasswordResetThrottle,
    RegisterThrottle,
    TokenRefreshThrottle,
)
from auth_app.tasks import trigger_mail_verification, trigger_password_reset
import django_rq
from auth_app.tasks import trigger_password_reset


class RegistrationView(generics.CreateAPIView):
    """POST /api/register/: create an inactive user and mail the activation link."""

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [RegisterThrottle]
    serializer_class = RegisterSerializer

    def create(self, request):
        """Save the user, enqueue the mail job and echo id, email and token."""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user = serializer.save()
            verify_token = default_token_generator.make_token(user)
            queue = django_rq.get_queue('default', autocommit=True)
            queue.enqueue(trigger_mail_verification, user.id, verify_token)

            data = {
                "user" : {
                    "id" : user.id,
                    "email" : user.email,
                },
                "token" : verify_token
            }

            return Response(data, status=status.HTTP_201_CREATED)



class LoginView(TokenObtainPairView):
    """POST /api/login/: check email and password, set the JWT cookies."""

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle]
    serializer_class = EmailTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        """Issue access and refresh cookies; the body never contains tokens."""
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0]) from e

        response = Response(serializer.validated_data, status=status.HTTP_200_OK)
        access_token = response.data.get("access")
        refresh_token =response.data.get("refresh")

        # Set cookie direkt on response access/token.
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,
            samesite="Lax"
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="Lax",
            max_age=86400
        )
        # Update response.data that no access/refresh token is in the response.
        response.data = {
            "detail" : "Login successful",
            "user" : {
                "id" : serializer.user.id,
                "username" :serializer.user.email
            }
        }

        return response

def delete_jwt_cookies(response:Response):
    """Expire both JWT cookies on the given response."""
    response.delete_cookie('access_token', path='/')
    response.delete_cookie('refresh_token', path='/')

class LogoutView(TokenBlacklistView):
    """POST /api/logout/: blacklist the refresh cookie and clear both cookies.

    No login is required: the refresh token itself is the proof of ownership,
    and an expired access cookie must not block the logout.
    """

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [LogoutThrottle]

    def post(self, request, *args, **kwargs) -> Response:
        """Blacklist the refresh token; an invalid one still clears the cookies."""
        try:
            refresh_token = request.COOKIES.get("refresh_token")
            serializer = self.get_serializer(data={"refresh" : refresh_token})
            serializer.is_valid(raise_exception=True)

            response = Response({"detail": "Log-Out successfully! All Tokens will be deleted. Refresh token is now invalid."}, status=status.HTTP_200_OK)
            delete_jwt_cookies(response)
            return response

        except TokenError:
            # If the token is already invalid/expired, still clear cookies
            response = Response({"detail": "Log-Out successfully! All Tokens will be deleted. Refresh token is now invalid."}, status=status.HTTP_200_OK)
            delete_jwt_cookies(response)
            return response

class CookieTokenRefreshView(TokenRefreshView):
    """POST /api/token/refresh/: trade the refresh cookie for a new access cookie."""

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [TokenRefreshThrottle]

    def post(self, request, *args, **kwargs):
        """400 without cookie, 401 with an invalid one (cookies cleared), else 200."""
        refresh_token = request.COOKIES.get("refresh_token")

        if refresh_token is None:
            return Response(
                {"message" : "Refresh token not found!"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data={"refresh":refresh_token})

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError:

            response = Response(
                {"message" : "Refresh token not found!"},
                status=status.HTTP_401_UNAUTHORIZED
            )
            delete_jwt_cookies(response)
            return response

        access_token = serializer.validated_data.get("access")
        response = Response({"detail" : "Token refreshed.", "access" : "new_access_token"})

        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,
            samesite="Lax"
        )

        return response


class UserActivationView(views.APIView):
    """GET /api/activate/<uidb64>/<token>/: activate the account from the mail link.

    Browsers (Accept: text/html) get the result page, API clients get JSON.
    """

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [ActivationThrottle]
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]

    def get(self, request, *args, **kwargs):
            """Decode the uid, check the token and set is_active."""
            try:
                uidb64_string = self.kwargs['uidb64']
                decoded_uidb64 = urlsafe_base64_decode(uidb64_string)
                user_id = force_str(decoded_uidb64)
                token = self.kwargs['token']

                user = User.objects.get(pk=user_id)
                if default_token_generator.check_token(user, token) is True:
                    user.is_active = True
                    user.save()

                    if request.accepted_renderer.format == 'html':

                        template_data = {
                            "title" : "Welcome to videoflix!",
                            "message" : "Account successfully activated.",
                            "FRONTEND_URL" : f"{os.getenv('FRONTEND_URL')}/pages/auth/login.html"
                        }
                        return Response(template_data, template_name='activation_result.html')
                    else:
                        return Response({"message": "Account successfully activated."}, status=status.HTTP_200_OK)
                else:
                    return self.failed(request)
            except (TypeError, ValueError, OverflowError, User.DoesNotExist):
                return self.failed(request)

    def failed(self, request):
        """400 for every invalid link: a page for browsers, JSON for API clients."""
        if request.accepted_renderer.format == 'html':
            template_data = {
                "title": "Activation failed",
                "message": "This activation link is invalid or has expired. "
                           "Please register again to receive a new one.",
                "FRONTEND_URL": f"{os.getenv('FRONTEND_URL')}/pages/auth/register.html",
            }
            return Response(
                template_data,
                template_name='activation_failed.html',
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(data={"error": "Activation failed!"}, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetView(views.APIView):
    """POST /api/password_reset/: enqueue the reset mail for a known address.

    The answer is always 200 so the endpoint cannot be used to find out
    which addresses are registered.
    """

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [PasswordResetThrottle]

    def post(self, request, *args, **kwargs):
        """Validate the address and hand the lookup and mail to the worker."""
        serializer = EmailSerializer(data=request.data)
        if serializer.is_valid():
            queue = django_rq.get_queue('default', autocommit=True)
            queue.enqueue(trigger_password_reset, serializer.validated_data['email'])

        return Response(data={"detail" : "An email has been sent to reset your password."})


class PasswordConfirmView(views.APIView):
    """POST /api/password_confirm/<uidb64>/<token>/: set the new password.

    The link becomes invalid by itself once the password changed, because
    the password hash is part of the token.
    """

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [PasswordConfirmThrottle]

    def post(self, request, *args, **kwargs):
        """Resolve the user, verify the token, then validate and save the password."""
        try:
            uidb64_string = self.kwargs['uidb64']
            decoded_uidb64 = urlsafe_base64_decode(uidb64_string)
            user_id = force_str(decoded_uidb64)
            token = self.kwargs['token']
            user = User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            # Broken uid or unknown user: same answer as an invalid token.
            return Response(data={"detail": "Invalid or expired link."}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            return Response(data={"detail": "Invalid or expired link."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ResetPasswordSerializer(data=request.data, context={"user" : user})
        # Field errors (missing or mismatching passwords) are rendered by DRF as 400.
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(data={"detail": "Your Password has been successfully reset."}, status=status.HTTP_200_OK)
        


       