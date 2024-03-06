from typing import Any, Dict, Optional

from rest_framework import serializers

from baserow.api.exceptions import RequestBodyValidationException
from baserow.contrib.builder.elements.registries import ElementType
from baserow.contrib.builder.pages.handler import PageHandler
from baserow.contrib.builder.types import ElementDict
from baserow.core.user_sources.handler import UserSourceHandler
from baserow_enterprise.builder.elements.models import AuthFormElement


class AuthFormElementType(ElementType):
    """
    Element that use the selected user source to generate the login form/buttons.
    """

    type = "auth_form"
    model_class = AuthFormElement
    allowed_fields = [
        "user_source",
        "user_source_id",
    ]
    serializer_field_names = ["user_source_id"]

    class SerializedDict(ElementDict):
        user_source_id: int

    @property
    def serializer_field_overrides(self):
        overrides = {
            "user_source_id": serializers.IntegerField(
                allow_null=True,
                default=None,
                help_text=AuthFormElement._meta.get_field("user_source").help_text,
                required=False,
            ),
        }

        return overrides

    def prepare_value_for_db(
        self, values: Dict, instance: Optional[AuthFormElement] = None
    ):
        if "user_source_id" in values:
            user_source_id = values.pop("user_source_id")
            if user_source_id is not None:
                user_source = UserSourceHandler().get_user_source(user_source_id)
                if instance:
                    current_page = PageHandler().get_page(instance.page_id)
                else:
                    current_page = values["page"]

                if current_page.builder_id != user_source.application_id:
                    raise RequestBodyValidationException(
                        {
                            "user_source_id": [
                                {
                                    "detail": "The provided user source doesn't belong "
                                    "to the same application.",
                                    "code": "invalid_user_source",
                                }
                            ]
                        }
                    )
                values["user_source"] = user_source
            else:
                values["user_source"] = None

        return super().prepare_value_for_db(values, instance)

    def deserialize_property(
        self,
        prop_name: str,
        value: Any,
        id_mapping: Dict[str, Any],
        **kwargs,
    ) -> Any:
        if prop_name == "user_source_id" and value:
            return id_mapping["user_sources"][value]

        return super().deserialize_property(prop_name, value, id_mapping)

    def get_pytest_params(self, pytest_data_fixture):
        return {
            "user_source_id": None,
        }
