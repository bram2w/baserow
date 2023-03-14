from typing import Dict
from urllib.parse import urlparse

from rest_framework import serializers

from baserow.api.user.serializers import NormalizedEmailField
from baserow.api.user.validators import language_validation


class SsoLoginRequestSerializer(serializers.Serializer):
    email = NormalizedEmailField(
        required=False, help_text="The email address of the user."
    )
    original = serializers.CharField(
        required=False,
        help_text="The relative part of URL that the user wanted to access.",
    )
    language = serializers.CharField(
        required=False,
        min_length=2,
        max_length=10,
        validators=[language_validation],
        help_text="An ISO 639 language code (with optional variant) "
        "selected by the user. Ex: en-GB.",
    )
    group_invitation_token = serializers.CharField(
        required=False,
        help_text="DEPRECATED: please use `workspace_invitation_token` as group is "
        "being renamed to workspace.",
    )
    workspace_invitation_token = serializers.CharField(
        required=False,
        help_text="If provided and valid, the user accepts the workspace invitation and"
        " will have access to the workspace after login or signing up.",
    )

    def to_representation(self, instance):
        group_token = instance.get("group_invitation_token", None)
        workspace_token = instance.get("workspace_invitation_token", None)

        if group_token is not None:
            if workspace_token is not None:
                raise serializers.ValidationError(
                    "Both a (deprecated) group_invitation_token and a "
                    "workspace_invitation_token were provided,"
                    "please just provide a valid workspace_invitation_token."
                )

            instance["workspace_invitation_token"] = group_token
            del instance["group_invitation_token"]
        return instance

    def validate_original(self, value):
        """Only relative URLs are allowed."""

        if urlparse(value).hostname:
            return None
        return value

    def to_internal_value(self, instance) -> Dict[str, str]:
        data = super().to_internal_value(instance)
        if "group_invitation_token" in data:
            data["workspace_invitation_token"] = data.pop("group_invitation_token")
        return {k: v for k, v in data.items() if v is not None}
