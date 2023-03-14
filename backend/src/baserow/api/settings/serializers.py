from rest_framework import serializers

from baserow.core.models import Settings


class SettingsSerializer(serializers.ModelSerializer):
    allow_global_group_creation = serializers.BooleanField(
        required=False,
        source="allow_global_workspace_creation",
        help_text="DEPRECATED: Please use the functionally identical "
        "`allow_global_workspace_creation` instead as this attribute is "
        "being removed in the future.",
    )  # GroupDeprecation
    allow_signups_via_group_invitations = serializers.BooleanField(
        required=False,
        source="allow_signups_via_workspace_invitations",
        help_text="DEPRECATED: Please use the functionally identical "
        "`allow_signups_via_workspace_invitations` instead as this attribute "
        "is being removed in the future.",
    )  # GroupDeprecation

    class Meta:
        model = Settings
        fields = (
            "allow_new_signups",
            "allow_signups_via_workspace_invitations",
            "allow_signups_via_group_invitations",  # GroupDeprecation
            "allow_reset_password",
            "allow_global_workspace_creation",
            "allow_global_group_creation",  # GroupDeprecation
            "account_deletion_grace_delay",
            "show_admin_signup_page",
            "track_group_usage",
        )
        extra_kwargs = {
            "allow_new_signups": {"required": False},
            "allow_signups_via_workspace_invitations": {"required": False},
            "allow_reset_password": {"required": False},
            "allow_global_workspace_creation": {"required": False},
            "account_deletion_grace_delay": {"required": False},
            "track_group_usage": {"required": False},
        }


class InstanceIdSerializer(serializers.ModelSerializer):
    class Meta:
        model = Settings
        fields = ("instance_id",)
        extra_kwargs = {
            "instance_id": {"read_only": True},
        }
