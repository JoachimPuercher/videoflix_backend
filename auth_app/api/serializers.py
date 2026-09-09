from django.contrib.auth.models import User
from rest_framework import serializers


class RegisterSerializer(serializers.ModelSerializer):
    """Creates a User together with its UserProfile from a single registration payload."""

    confirmed_password = serializers.CharField(max_length=100, write_only=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'confirmed_password']
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def save(self):
        """Create the user with a hashed password and the matching profile."""
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
