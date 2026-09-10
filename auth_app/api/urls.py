from django.urls import path
from .views import RegistrationView, UserActivationView, LoginView, LogoutView, CookieTokenRefreshView, PasswordResetView


urlpatterns = [
    path('register/', RegistrationView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', CookieTokenRefreshView.as_view(), name='token_refresh'),
    path('activate/<str:uidb64>/<str:token>/', UserActivationView.as_view(), name='activate'),
    path('password_reset/', PasswordResetView.as_view(), name='password_reset'),
]