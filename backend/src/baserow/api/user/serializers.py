from rest_framework import serializers
from rest_framework_jwt.serializers import JSONWebTokenSerializer

from django.contrib.auth import get_user_model
from django.contrib.auth.models import update_last_login

from baserow.api.groups.invitations.serializers import UserGroupInvitationSerializer
from baserow.core.user.utils import normalize_email_address
from baserow.core.models import Template, UserLogEntry

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("first_name", "username", "password", "is_staff")
        extra_kwargs = {
            "password": {"write_only": True},
            "is_staff": {"read_only": True},
        }


class RegisterSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=32)
    email = serializers.EmailField(
        help_text="The email address is also going to be the username."
    )
    password = serializers.CharField(max_length=256)
    authenticate = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Indicates whether an authentication token should be generated and "
        "be included in the response.",
    )
    group_invitation_token = serializers.CharField(
        required=False,
        help_text="If provided and valid, the user accepts the group invitation and "
        "will have access to the group after signing up.",
    )
    template_id = serializers.PrimaryKeyRelatedField(
        required=False,
        default=None,
        queryset=Template.objects.all(),
        help_text="The id of the template that must be installed after creating the "
        "account. This only works if the `group_invitation_token` param is not "
        "provided.",
    )


class SendResetPasswordEmailBodyValidationSerializer(serializers.Serializer):
    email = serializers.EmailField(
        help_text="The email address of the user that has requested a password reset."
    )
    base_url = serializers.URLField(
        help_text="The base URL where the user can reset his password. The reset "
        "token is going to be appended to the base_url (base_url "
        "'/token')."
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

    def validate(self, attrs):
        """
        This serializer is only used by the ObtainJSONWebToken view which is only used
        to generate a new token. When that happens we want to update the user's last
        login timestamp.
        """

        # In the future, when migrating away from the JWT implementation, we want to
        # respond with machine readable error codes when authentication fails.
        validated_data = super().validate(attrs)
        update_last_login(None, validated_data["user"])
        UserLogEntry.objects.create(actor=validated_data["user"], action="SIGNED_IN")
        # Call the user_signed_in method for each plugin that is un the registry to
        # notify all plugins that a user has signed in.
        from baserow.core.registries import plugin_registry

        for plugin in plugin_registry.registry.values():
            plugin.user_signed_in(validated_data["user"])
        return validated_data


class DashboardSerializer(serializers.Serializer):
    group_invitations = UserGroupInvitationSerializer(many=True)
