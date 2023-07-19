from typing import Any, Dict

from django.contrib.auth.models import AbstractUser

from baserow.api.user.serializers import SubjectUserSerializer
from baserow.contrib.integrations.local_baserow.models import LocalBaserowIntegration
from baserow.core.integrations.registries import IntegrationType


class LocalBaserowIntegrationType(IntegrationType):
    type = "local_baserow"
    model_class = LocalBaserowIntegration

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

    def export_serialized(self, instance: Any) -> Dict[str, Any]:
        return super().export_serialized(instance)

    def import_serialized(
        self, parent: Any, serialized_values: Dict[str, Any], id_mapping: Dict
    ) -> Any:
        return super().import_serialized(parent, serialized_values, id_mapping)

    def enhance_queryset(self, queryset):
        return queryset.select_related("authorized_user")
