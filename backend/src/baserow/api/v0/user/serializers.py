from rest_framework import serializers
from django.contrib.auth import get_user_model

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
    email = serializers.EmailField()
    password = serializers.CharField(max_length=32)
    authenticate = serializers.BooleanField(required=False, default=False)


class SendResetPasswordEmailBodyValidationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    base_url = serializers.URLField()


class ResetPasswordBodyValidationSerializer(serializers.Serializer):
    token = serializers.CharField()
    password = serializers.CharField()
