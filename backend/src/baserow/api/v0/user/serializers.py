from rest_framework import serializers
from rest_framework_jwt.serializers import JSONWebTokenSerializer

from django.contrib.auth import get_user_model

from baserow.core.user.utils import normalize_email_address

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('first_name', 'username', 'password')
        extra_kwargs = {
            'password': {
                'write_only': True
            }
        }


class RegisterSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=32)
    email = serializers.EmailField(
        help_text='The email address is also going to be the username.'
    )
    password = serializers.CharField(max_length=32)
    authenticate = serializers.BooleanField(
        required=False,
        default=False,
        help_text='Indicates whether an authentication token should be generated and '
                  'be included in the response.'
    )


class SendResetPasswordEmailBodyValidationSerializer(serializers.Serializer):
    email = serializers.EmailField(
        help_text='The email address of the user that has requested a password reset.'
    )
    base_url = serializers.URLField(
        help_text='The base URL where the user can reset his password. The reset '
                  'token is going to be appended to the base_url (base_url '
                  '\'/token\').'
    )


class ResetPasswordBodyValidationSerializer(serializers.Serializer):
    token = serializers.CharField()
    password = serializers.CharField()


class ChangePasswordBodyValidationSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField()


class NormalizedEmailField(serializers.EmailField):
    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        return normalize_email_address(data)


class NormalizedEmailWebTokenSerializer(JSONWebTokenSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields[self.username_field] = NormalizedEmailField()
