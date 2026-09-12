"""Serializers of the auth API: registration, login, password reset."""

from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class RegisterSerializer(serializers.ModelSerializer):
    """Create an inactive User from email, password and confirmed_password."""

    confirmed_password = serializers.CharField(max_length=100, write_only=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'confirmed_password']
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def save(self):
        """Create the user with a hashed password; the email doubles as username."""
        user = User(
            username=self.validated_data['email'],
            email=self.validated_data['email'],
        )
        user.set_password(self.validated_data['password'])
        user.is_active = False
        user.save()

        return user

    def validate_email(self, value):
        """Reject duplicate addresses and store them lower cased."""
        new_mail = value.lower()
        if User.objects.filter(email=new_mail).exists():
            raise serializers.ValidationError('Email already exists')
        else:
            return new_mail

    def validate(self, values):
        """Both password fields have to match."""
        if values['password'] != values['confirmed_password']:
            raise serializers.ValidationError('Password do not match')
        else:
            return values


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Simple JWT login with email instead of username.

    The parent adds a required `username` field at runtime; it is removed
    here and looked up from the email before the parent issues the tokens.
    """

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        if 'username' in self.fields:
            self.fields.pop('username')

    def validate(self, attrs):
        """Reject unknown address, wrong password and inactive account alike.

        One message and one status (401) for all three, so the login does
        not reveal whether an address is registered.
        """
        email = attrs.get("email")
        password = attrs.get("password")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise AuthenticationFailed("Invalid email or password.")

        if not user.check_password(password) or not user.is_active:
            raise AuthenticationFailed("Invalid email or password.")

        data = super().validate({"username": user.username, "password": password})
        return data


class EmailSerializer(serializers.Serializer):
    """Validate the address of a password reset request; nothing is saved."""

    email = serializers.EmailField(write_only=True)


class ResetPasswordSerializer(serializers.Serializer):
    """Set a new password for the user passed in context["user"]."""

    confirm_password = serializers.CharField(max_length=100, write_only=True)
    new_password = serializers.CharField(max_length=100, write_only=True)

    def validate(self, values):
        """Both password fields have to match."""
        if values['new_password'] != values['confirm_password']:
            raise serializers.ValidationError('Password do not match')
        else:
            return values

    def save(self):
        """Hash and store the new password; only that column is written."""
        user = self.context["user"]
        user.set_password(self.validated_data['new_password'])
        user.save(update_fields=["password"])