from typing import Any, Dict, Optional

from django.contrib.auth.models import AbstractUser

from rest_framework import serializers

from baserow.api.exceptions import RequestBodyValidationException
from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.table.handler import TableHandler
from baserow.core.user_sources.registries import UserSourceType
from baserow.core.user_sources.types import UserSourceDict, UserSourceSubClass
from baserow_enterprise.integrations.local_baserow.models import LocalBaserowUserSource


class LocalBaserowUserSourceType(UserSourceType):
    type = "local_baserow"
    model_class = LocalBaserowUserSource

    class SerializedDict(UserSourceDict):
        table_id: int
        email_field_id: int
        name_field_id: int

    serializer_field_names = ["table_id", "email_field_id", "name_field_id"]
    allowed_fields = ["table", "email_field", "name_field"]

    serializer_field_overrides = {
        "table_id": serializers.IntegerField(
            required=False,
            allow_null=True,
            help_text="The id of the Baserow table we want the data for.",
        ),
        "email_field_id": serializers.IntegerField(
            required=False,
            allow_null=True,
            help_text="The id of the field to use as email for the user account.",
        ),
        "name_field_id": serializers.IntegerField(
            required=False,
            allow_null=True,
            help_text="The id of the field that contains the user name.",
        ),
    }

    def prepare_values(
        self,
        values: Dict[str, Any],
        user: AbstractUser,
        instance: Optional[UserSourceSubClass] = None,
    ) -> Dict[str, Any]:
        """Load the table instance instead of the ID."""

        # We resolve the integration first
        values = super().prepare_values(values, user)

        if "table_id" in values:
            table_id = values.pop("table_id")
            if table_id is not None:
                table = TableHandler().get_table(table_id)

                # check that table belongs to same workspace
                integration_to_check = None
                if instance:
                    integration_to_check = instance.integration
                if "integration" in values:
                    integration_to_check = values["integration"]

                if (
                    not integration_to_check
                    or table.database.workspace_id
                    != integration_to_check.application.workspace_id
                ):
                    raise RequestBodyValidationException(
                        {
                            "table_id": [
                                {
                                    "detail": f"The table with ID {table.id} is not "
                                    "related to the given workspace.",
                                    "code": "invalid_table",
                                }
                            ]
                        }
                    )
                values["table"] = table

                # Reset the fields if the table has changed
                if (
                    "email_field_id" not in values
                    and instance
                    and instance.email_field_id
                    and instance.email_field_id.table_id != table_id
                ):
                    values["email_field_id"] = None

                if (
                    "name_field_id" not in values
                    and instance
                    and instance.name_field_id
                    and instance.name_field_id.table_id != table_id
                ):
                    values["name_field_id"] = None
            else:
                values["table"] = None

        table_to_check = None

        if instance:
            table_to_check = instance.table
        if "table" in values:
            table_to_check = values["table"]

        if "email_field_id" in values:
            email_field_id = values.pop("email_field_id")
            if email_field_id is not None:
                field = FieldHandler().get_field(email_field_id)

                if not table_to_check or field.table_id != table_to_check.id:
                    raise RequestBodyValidationException(
                        {
                            "email_field_id": [
                                {
                                    "detail": f"The field with ID {email_field_id} is "
                                    "not related to the given table.",
                                    "code": "invalid_field",
                                }
                            ]
                        }
                    )
                values["email_field"] = field
            else:
                values["email_field"] = None

        if "name_field_id" in values:
            name_field_id = values.pop("name_field_id")
            if name_field_id is not None:
                field = FieldHandler().get_field(name_field_id)

                if not table_to_check or field.table_id != table_to_check.id:
                    raise RequestBodyValidationException(
                        {
                            "name_field_id": [
                                {
                                    "detail": f"The field with ID {name_field_id} is "
                                    "not related to the given table.",
                                    "code": "invalid_field",
                                }
                            ]
                        }
                    )
                values["name_field"] = field
            else:
                values["name_field"] = None

        return values

    def deserialize_property(
        self,
        prop_name: str,
        value: Any,
        id_mapping: Dict[str, Dict[int, int]],
        **kwargs,
    ) -> Any:
        """
        Map table, email_field and name_field ids.
        """

        if prop_name == "table_id":
            return id_mapping.get("database_tables", {}).get(value, value)

        if prop_name == "email_field_id":
            return id_mapping.get("database_fields", {}).get(value, value)

        if prop_name == "name_field_id":
            return id_mapping.get("database_fields", {}).get(value, value)

        return super().deserialize_property(prop_name, value, id_mapping, **kwargs)
