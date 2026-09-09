from django.urls import path
from .views import RegistrationView, UserActivationView, LoginView


urlpatterns = [
    path('register/', RegistrationView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    # path('login/', LogoutView.as_view(), name='logout'),
    path('activate/<str:uidb64>/<str:token>/', UserActivationView.as_view(), name='activate'),
]