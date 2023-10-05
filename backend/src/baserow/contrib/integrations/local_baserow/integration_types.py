from typing import Any, Dict, Optional

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db.models import QuerySet

from baserow.api.user.serializers import SubjectUserSerializer
from baserow.contrib.database.models import Table
from baserow.contrib.database.operations import ListTablesDatabaseTableOperationType
from baserow.contrib.integrations.api.local_baserow.serializers import (
    LocalBaserowContextDataSerializer,
)
from baserow.contrib.integrations.local_baserow.models import LocalBaserowIntegration
from baserow.core.handler import CoreHandler
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

    serializer_field_names = ["context_data", "authorized_user"]
    allowed_fields = ["authorized_user"]

    serializer_field_overrides = {
        "context_data": LocalBaserowContextDataSerializer(read_only=True),
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

    def get_context_data(self, instance: LocalBaserowIntegration) -> Optional[Dict]:
        return {
            "databases": LocalBaserowIntegrationType.get_local_baserow_databases(
                instance
            )
        }

    @staticmethod
    def get_local_baserow_databases(integration: LocalBaserowIntegration) -> QuerySet:
        """
        This method returns the databases that the user has access to in a query
        efficient way while also checking for permissions. It will do so by fetching
        all the tables at ones, and then group them by database.

        A side effect of this solution is that databases without tables don't show up
        in this list.
        """

        databases = []

        if (
            integration.application.workspace_id is not None
            and integration.specific.authorized_user is not None
        ):
            user = integration.specific.authorized_user
            workspace = integration.application.workspace

            tables_queryset = Table.objects.filter(
                database__workspace_id=workspace.id, database__workspace__trashed=False
            ).select_related("database", "database__workspace")

            tables = CoreHandler().filter_queryset(
                user,
                ListTablesDatabaseTableOperationType.type,
                tables_queryset,
                workspace=integration.application.workspace,
                context=None,
            )

            for table in tables:
                if table.database not in databases:
                    table.database.tables = []
                    databases.append(table.database)
                database = databases[databases.index(table.database)]
                database.tables.append(table)

            databases.sort(key=lambda x: x.order)

        return databases
