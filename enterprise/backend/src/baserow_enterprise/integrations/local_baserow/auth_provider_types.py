from typing import Any, Dict, Optional, Tuple

from django.contrib.auth.models import AbstractUser

from rest_framework import serializers

from baserow.api.exceptions import RequestBodyValidationException
from baserow.contrib.database.fields.exceptions import FieldDoesNotExist
from baserow.contrib.database.fields.handler import FieldHandler
from baserow.core.app_auth_providers.auth_provider_types import AppAuthProviderType
from baserow.core.app_auth_providers.types import AppAuthProviderTypeDict
from baserow.core.auth_provider.types import AuthProviderModelSubClass
from baserow.core.user_sources.types import UserSourceSubClass
from baserow_enterprise.integrations.local_baserow.models import (
    LocalBaserowPasswordAppAuthProvider,
)
from baserow_enterprise.integrations.local_baserow.user_source_types import (
    LocalBaserowUserSourceType,
)


class LocalBaserowPasswordAppAuthProviderType(AppAuthProviderType):
    type = "local_baserow_password"
    model_class = LocalBaserowPasswordAppAuthProvider
    compatible_user_source_types = [LocalBaserowUserSourceType.type]

    serializer_field_names = ["password_field_id"]
    allowed_fields = ["password_field"]

    serializer_field_overrides = {
        "password_field_id": serializers.IntegerField(
            required=False,
            allow_null=True,
            help_text="The id of the field to use as password for the user account.",
        ),
    }

    class SerializedDict(AppAuthProviderTypeDict):
        password_field_id: int

    def can_create_new_providers(
        self, user_source: Optional[UserSourceSubClass] = None, **kwargs
    ) -> bool:
        """
        Returns True if it's possible to create an authentication provider of this type.
        """

        return not LocalBaserowPasswordAppAuthProvider.objects.filter(
            user_source=user_source
        ).exists()

    def prepare_values(
        self,
        values: Dict[str, Any],
        user: AbstractUser,
        instance: Optional[LocalBaserowPasswordAppAuthProvider] = None,
    ) -> Dict[str, Any]:
        """Load the table instance instead of the ID."""

        # We resolve the user_source first
        values = super().prepare_values(values, user)

        table_to_check = None

        if instance:
            table_to_check = instance.user_source.specific.table
        if "user_source" in values:
            table_to_check = values["user_source"].table

        # Check that the password field belongs to the user_source table
        if "password_field_id" in values:
            field_id = values.pop("password_field_id")
            if field_id is not None:
                if not table_to_check:
                    raise RequestBodyValidationException(
                        {
                            "password_field_id": [
                                {
                                    "detail": "Please select a table before selecting "
                                    "this field.",
                                    "code": "missing_table",
                                }
                            ]
                        }
                    )

                try:
                    field = FieldHandler().get_field(field_id)
                except FieldDoesNotExist as exc:
                    raise RequestBodyValidationException(
                        {
                            "password_field_id": [
                                {
                                    "detail": "The provided Id doesn't exist.",
                                    "code": "invalid_field",
                                }
                            ]
                        }
                    ) from exc

                if not table_to_check or field.table_id != table_to_check.id:
                    raise RequestBodyValidationException(
                        {
                            "password_field_id": [
                                {
                                    "detail": f"The field with ID {field_id} is "
                                    "not related to the given table.",
                                    "code": "invalid_field",
                                }
                            ]
                        }
                    )
                values["password_field"] = field
            else:
                values["password_field"] = None

        return values

    def after_user_source_update(
        self,
        user: "AbstractUser",
        instance: LocalBaserowPasswordAppAuthProvider,
        user_source,
    ):
        """
        Removes password field if table id has changed.
        """

        if (
            instance.password_field_id
            and instance.password_field.table_id != user_source.table_id
        ):
            instance.password_field = None
            instance.save()

    def get_login_options(self, **kwargs) -> Dict[str, Any]:
        """
        Not implemented yet.
        """

        return {}

    def get_or_create_user_and_sign_in(
        self, auth_provider: AuthProviderModelSubClass, user_info: Dict[str, Any]
    ) -> Tuple[AbstractUser, bool]:
        """
        Not implemented yet.
        """
