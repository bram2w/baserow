from typing import List

from django.conf import settings
from django.contrib.auth import get_user_model
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework_jwt.serializers import JSONWebTokenSerializer

from baserow.api.groups.invitations.serializers import UserGroupInvitationSerializer
from baserow.api.mixins import UnknownFieldRaisesExceptionSerializerMixin
from baserow.api.user.validators import password_validation, language_validation
from baserow.core.action.models import Action
from baserow.core.action.registries import action_scope_registry, ActionScopeStr
from baserow.core.models import Template
from baserow.core.user.utils import normalize_email_address
from baserow.core.user.handler import UserHandler

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    language = serializers.CharField(
        source="profile.language",
        required=False,
        min_length=2,
        max_length=10,
        validators=[language_validation],
        help_text="An ISO 639 language code (with optional variant) "
        "selected by the user. Ex: en-GB.",
    )

    class Meta:
        model = User
        fields = (
            "first_name",
            "username",
            "password",
            "is_staff",
            "id",
            "language",
        )
        extra_kwargs = {
            "password": {"write_only": True},
            "is_staff": {"read_only": True},
            "id": {"read_only": True},
        }


class RegisterSerializer(serializers.Serializer):
    name = serializers.CharField(min_length=2, max_length=150)
    email = serializers.EmailField(
        help_text="The email address is also going to be the username."
    )
    password = serializers.CharField(validators=[password_validation])
    language = serializers.CharField(
        required=False,
        default=settings.LANGUAGE_CODE,
        min_length=2,
        max_length=10,
        validators=[language_validation],
        help_text="An ISO 639 language code (with optional variant) "
        "selected by the user. Ex: en-GB.",
    )
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


def get_action_scopes_request_serializer():
    attrs = {}

    for scope_type in action_scope_registry.get_all():
        attrs[scope_type.type] = scope_type.get_request_serializer_field()

    return type(
        "ActionScopesRequestSerializer",
        (serializers.Serializer, UnknownFieldRaisesExceptionSerializerMixin),
        attrs,
    )


ActionScopesSerializer = get_action_scopes_request_serializer()


class UndoRedoRequestSerializer(serializers.Serializer):
    scopes = ActionScopesSerializer(
        required=True,
        help_text="A JSON object with keys and values representing the various action "
        "scopes to include when undoing or redoing. Every action in Baserow will "
        "be associated with a action scope, when undoing/redoing only actions "
        "which match any of the provided scope key:value pairs will included when "
        "this endpoint picks the next action to undo/redo.",
    )

    @property
    def data(self) -> List[ActionScopeStr]:
        scope_list = []
        for scope_type_str, scope_value in self.validated_data["scopes"].items():
            if scope_value:
                scope_type = action_scope_registry.get(scope_type_str)
                scope_str = scope_type.valid_serializer_value_to_scope_str(scope_value)
                if scope_str is not None:
                    scope_list.append(scope_str)
        return scope_list


@extend_schema_field(OpenApiTypes.STR)
class UndoRedoResultCodeField(serializers.Field):
    # Please keep code values in sync with
    # web-frontend/modules/core/utils/undoRedoConstants.js:UNDO_REDO_RESULT_CODES
    NOTHING_TO_DO = "NOTHING_TO_DO"
    SUCCESS = "SUCCESS"
    SKIPPED_DUE_TO_ERROR = "SKIPPED_DUE_TO_ERROR"

    def __init__(self, *args, **kwargs):
        kwargs["help_text"] = (
            "Indicates the result of the undo/redo operation. Will be "
            f"'{self.SUCCESS}' on success, '{self.NOTHING_TO_DO}' when "
            "there is no action to undo/redo and "
            f"'{self.SKIPPED_DUE_TO_ERROR}' when the undo/redo failed due "
            "to a conflict or error and was skipped over."
        )
        super().__init__(*args, **kwargs)

    def get_attribute(self, instance):
        return instance["actions"]

    def to_representation(self, actions):
        if not actions:
            return self.NOTHING_TO_DO
        if actions[0].has_error():
            return self.SKIPPED_DUE_TO_ERROR
        else:
            return self.SUCCESS


class UndoRedoActionSerializer(serializers.ModelSerializer):

    action_type = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
        source="type",
        initial=None,
        help_text="If an action was undone/redone/skipped due to an error this field "
        "will contain the type of the action that was undone/redone.",
    )
    action_scope = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
        source="scope",
        initial=None,
        help_text="If an action was undone/redone/skipped due to an error this field "
        "will contain the scope of the action that was undone/redone.",
    )

    class Meta:
        model = Action
        fields = ("action_type", "action_scope")


class UndoRedoResponseSerializer(serializers.Serializer):
    actions = UndoRedoActionSerializer(many=True)
    result_code = UndoRedoResultCodeField()


class AccountSerializer(serializers.Serializer):
    """
    This serializer must be kept in sync with `UserSerializer`.
    """

    first_name = serializers.CharField(min_length=2, max_length=150)
    language = serializers.CharField(
        source="profile.language",
        required=False,
        min_length=2,
        max_length=10,
        validators=[language_validation],
        help_text="An ISO 639 language code (with optional variant) "
        "selected by the user. Ex: en-GB.",
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
    password = serializers.CharField(validators=[password_validation])


class ChangePasswordBodyValidationSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField(validators=[password_validation])


class DeleteUserBodyValidationSerializer(serializers.Serializer):
    password = serializers.CharField()


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

        user = validated_data["user"]
        if not user.is_active:
            msg = "User account is disabled."
            raise serializers.ValidationError(msg)

        UserHandler().user_signed_in(user)

        return validated_data


class DashboardSerializer(serializers.Serializer):
    group_invitations = UserGroupInvitationSerializer(many=True)
