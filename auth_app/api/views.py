from django.shortcuts import render
from rest_framework import generics, status, views
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated, SAFE_METHODS
from rest_framework.response import Response
from .serializers import RegisterSerializer, EmailTokenObtainPairSerializer
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_str
from django.contrib.auth.models import User
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenBlacklistView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.renderers import TemplateHTMLRenderer
import os

# LoginSerializer, UserSerializer
# from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenBlacklistView
# from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
# from .authentication import JWTCookieAuthentication



from auth_app.tasks import send_order_confirmation



class RegistrationView(generics.CreateAPIView):
    """Registers a new user."""

    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        verify_token = default_token_generator.make_token(user)
        send_order_confirmation(user, verify_token)

        data = {
            "user" : {
                "id" : user.id,
                "email" : user.email,
            },
            "token" : verify_token
        }

        return Response(data, status=status.HTTP_201_CREATED)


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


class LoginView(TokenObtainPairView):
# Self created class from the simplejwt class.

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
            samesite="Lax"
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

