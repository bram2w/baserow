from typing import Any, Dict

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser

from baserow.api.user.serializers import SubjectUserSerializer
from baserow.contrib.integrations.local_baserow.models import LocalBaserowIntegration
from baserow.core.integrations.models import Integration
from baserow.core.integrations.registries import IntegrationType
from baserow.core.integrations.types import IntegrationDict
from baserow.core.models import Application

User = get_user_model()


class LocalBaserowIntegrationType(IntegrationType):
    type = "local_baserow"
    model_class = LocalBaserowIntegration

    class SerializedDict(IntegrationDict):
        authorized_user_username: str

    serializer_field_names = ["authorized_user"]
    allowed_fields = ["authorized_user"]

    serializer_field_overrides = {
        "authorized_user": SubjectUserSerializer(read_only=True),
    }

    request_serializer_field_names = []
    request_serializer_field_overrides = {}

    def prepare_values(
        self, values: Dict[str, Any], user: AbstractUser
    ) -> Dict[str, Any]:
        """Add the logged in user by default"""

        values["authorized_user"] = user

        return super().prepare_values(values, user)

    def get_property_for_serialization(self, integration: Integration, prop_name: str):
        """
        Replace the authorized user property with it's username. Better when loading the
        data later.
        """

        if prop_name == "authorized_user_username":
            if integration.authorized_user:
                return integration.authorized_user.username
            return None

        return super().get_property_for_serialization(integration, prop_name)

    def import_serialized(
        self,
        application: Application,
        serialized_values: Dict[str, Any],
        id_mapping: Dict,
        cache=None,
    ) -> LocalBaserowIntegration:
        """
        Imports a serialized integration. Handles the user part with a cache for
        better performances.
        """

        if cache is None:
            cache = {}

        if "workspace_users" not in cache:
            # In order to prevent a lot of lookup queries in the through table, we want
            # to fetch all the users and add it to a temporary in memory cache
            # containing a mapping of user per email
            cache["workspace_users"] = {
                user.username: user
                for user in User.objects.filter(
                    workspaceuser__workspace_id=id_mapping["import_workspace_id"]
                )
            }

        username = serialized_values.pop("authorized_user_username", None)

        if username:
            serialized_values["authorized_user"] = cache["workspace_users"].get(
                username, None
            )

        return super().import_serialized(
            application, serialized_values, id_mapping, cache
        )

    def enhance_queryset(self, queryset):
        return queryset.select_related("authorized_user")
