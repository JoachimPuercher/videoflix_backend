from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .serializers import RegisterSerializer
# LoginSerializer, UserSerializer
# from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenBlacklistView
# from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
# from .authentication import JWTCookieAuthentication



from auth_app.tasks import send_order_confirmation



class RegistrationView(generics.CreateAPIView):
    """Registers a new user."""

    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        send_order_confirmation(user)

        data = {
            "user" : {
                "id" : user.id,
                "email" : user.email,
            },
            "token" : "token"
        }

        return Response(data, status=status.HTTP_201_CREATED)