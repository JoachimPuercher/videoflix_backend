from django.shortcuts import render
from rest_framework import generics, status, views
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated, SAFE_METHODS
from rest_framework.response import Response
from .serializers import RegisterSerializer, EmailTokenObtainPairSerializer, EmailSerializer
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_str
from django.contrib.auth.models import User
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenBlacklistView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.renderers import TemplateHTMLRenderer
import os
from .authentication import JWTCookieAuthentication
from auth_app.tasks import trigger_mail_verification, trigger_password_reset
import django_rq
from auth_app.tasks import trigger_password_reset


class RegistrationView(generics.CreateAPIView):
    """Registers a new user."""

    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request):
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
# Self created class from the simplejwt class.

    authentication_classes = []
    permission_classes = [AllowAny]

    serializer_class = EmailTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
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
    response.delete_cookie('access_token', path='/')
    response.delete_cookie('refresh_token', path='/')

class LogoutView(TokenBlacklistView):

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs) -> Response:

        print(request.COOKIES)
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

    authentication_classes = []
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):

        refresh_token = request.COOKIES.get("refresh_token")

        if refresh_token is None:
            return Response(
                {"message" : "Refresh token not found!"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data={"refresh":refresh_token})

        try:
            serializer.is_valid(raise_exception=True)
        except:

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

    authentication_classes = []
    permission_classes = [AllowAny]
    renderer_classes = [TemplateHTMLRenderer]

    def get(self, request, *args, **kwargs):

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
                            "FRONTEND_URL" : f"{os.getenv('FRONTEND_URL')}pages/auth/login.html"
                        }
                        return Response(template_data, template_name='activation_result.html')
                    else:
                        return Response({"message": "Account successfully activated."}, status=status.HTTP_200_OK)
                else:
                    return Response(data={"error" : "Activation failed!"}, status=status.HTTP_400_BAD_REQUEST)    
            except:
                return Response(data={"error" : "Activation failed!"}, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetView(views.APIView):

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):

        serializer = EmailSerializer(data=request.data)
        if serializer.is_valid():
            queue = django_rq.get_queue('default', autocommit=True)
            queue.enqueue(trigger_password_reset, serializer.validated_data['email'])

        return Response(data={"detail" : "An email has been sent to reset your password."})
