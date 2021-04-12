from django.db import transaction

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import permission_classes as method_permission_classes

from drf_spectacular.utils import extend_schema
from drf_spectacular.openapi import OpenApiParameter, OpenApiTypes

from baserow.api.decorators import validate_body_custom_fields, map_exceptions
from baserow.api.utils import validate_data_custom_fields, type_from_data_or_registry
from baserow.api.errors import ERROR_USER_NOT_IN_GROUP
from baserow.api.utils import PolymorphicCustomFieldRegistrySerializer
from baserow.api.schemas import get_error_schema
from baserow.core.exceptions import UserNotInGroup
from baserow.contrib.database.api.tables.errors import ERROR_TABLE_DOES_NOT_EXIST
from baserow.contrib.database.table.handler import TableHandler
from baserow.contrib.database.table.exceptions import TableDoesNotExist
from baserow.contrib.database.api.fields.errors import (
    ERROR_CANNOT_DELETE_PRIMARY_FIELD,
    ERROR_CANNOT_CHANGE_FIELD_TYPE,
    ERROR_FIELD_DOES_NOT_EXIST,
)
from baserow.contrib.database.fields.exceptions import (
    CannotDeletePrimaryField,
    CannotChangeFieldType,
    FieldDoesNotExist,
)
from baserow.contrib.database.fields.models import Field
from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.fields.registries import field_type_registry

from .serializers import FieldSerializer, CreateFieldSerializer, UpdateFieldSerializer


class FieldsView(APIView):
    permission_classes = (IsAuthenticated,)

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]

        return super().get_permissions()

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="table_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Returns only the fields of the table related to the "
                "provided value.",
            )
        ],
        tags=["Database table fields"],
        operation_id="list_database_table_fields",
        description=(
            "Lists all the fields of the table related to the provided parameter if "
            "the user has access to the related database's group. If the group is "
            "related to a template, then this endpoint will be publicly accessible. A "
            "table consists of fields and each field can have a different type. Each "
            "type can have different properties. A field is comparable with a regular "
            "table's column."
        ),
        responses={
            200: PolymorphicCustomFieldRegistrySerializer(
                field_type_registry, FieldSerializer, many=True
            ),
            400: get_error_schema(["ERROR_USER_NOT_IN_GROUP"]),
            404: get_error_schema(["ERROR_TABLE_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            TableDoesNotExist: ERROR_TABLE_DOES_NOT_EXIST,
            UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
        }
    )
    @method_permission_classes([AllowAny])
    def get(self, request, table_id):
        """
        Responds with a list of serialized fields that belong to the table if the user
        has access to that group.
        """

        table = TableHandler().get_table(table_id)
        table.database.group.has_user(
            request.user, raise_error=True, allow_if_template=True
        )
        fields = Field.objects.filter(table=table).select_related("content_type")

        data = [
            field_type_registry.get_serializer(field, FieldSerializer).data
            for field in fields
        ]
        return Response(data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="table_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Creates a new field for the provided table related to the "
                "value.",
            )
        ],
        tags=["Database table fields"],
        operation_id="create_database_table_field",
        description=(
            "Creates a new field for the table related to the provided `table_id` "
            "parameter if the authorized user has access to the related database's "
            "group. Depending on the type, different properties can optionally be "
            "set."
        ),
        request=PolymorphicCustomFieldRegistrySerializer(
            field_type_registry, CreateFieldSerializer
        ),
        responses={
            200: PolymorphicCustomFieldRegistrySerializer(
                field_type_registry, FieldSerializer
            ),
            400: get_error_schema(
                ["ERROR_USER_NOT_IN_GROUP", "ERROR_REQUEST_BODY_VALIDATION"]
            ),
            404: get_error_schema(["ERROR_TABLE_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @validate_body_custom_fields(
        field_type_registry, base_serializer_class=CreateFieldSerializer
    )
    @map_exceptions(
        {
            TableDoesNotExist: ERROR_TABLE_DOES_NOT_EXIST,
            UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
        }
    )
    def post(self, request, data, table_id):
        """Creates a new field for a table."""

        type_name = data.pop("type")
        field_type = field_type_registry.get(type_name)
        table = TableHandler().get_table(table_id)
        table.database.group.has_user(request.user, raise_error=True)

        # Because each field type can raise custom exceptions while creating the
        # field we need to be able to map those to the correct API exceptions which are
        # defined in the type.
        with field_type.map_api_exceptions():
            field = FieldHandler().create_field(request.user, table, type_name, **data)

        serializer = field_type_registry.get_serializer(field, FieldSerializer)
        return Response(serializer.data)


class FieldView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="field_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Returns the field related to the provided value.",
            )
        ],
        tags=["Database table fields"],
        operation_id="get_database_table_field",
        description=(
            "Returns the existing field if the authorized user has access to the "
            "related database's group. Depending on the type different properties"
            "could be returned."
        ),
        responses={
            200: PolymorphicCustomFieldRegistrySerializer(
                field_type_registry, FieldSerializer
            ),
            400: get_error_schema(["ERROR_USER_NOT_IN_GROUP"]),
            404: get_error_schema(["ERROR_FIELD_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            FieldDoesNotExist: ERROR_FIELD_DOES_NOT_EXIST,
            UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
        }
    )
    def get(self, request, field_id):
        """Selects a single field and responds with a serialized version."""

        field = FieldHandler().get_field(field_id)
        field.table.database.group.has_user(request.user, raise_error=True)
        serializer = field_type_registry.get_serializer(field, FieldSerializer)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="field_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Updates the field related to the provided value.",
            )
        ],
        tags=["Database table fields"],
        operation_id="update_database_table_field",
        description=(
            "Updates the existing field if the authorized user has access to the "
            "related database's group. The type can also be changed and depending on "
            "that type, different additional properties can optionally be set. If you "
            "change the field type it could happen that the data conversion fails, in "
            "that case the `ERROR_CANNOT_CHANGE_FIELD_TYPE` is returned, but this "
            "rarely happens. If a data value cannot be converted it is set to `null` "
            "so data might go lost."
        ),
        request=PolymorphicCustomFieldRegistrySerializer(
            field_type_registry, UpdateFieldSerializer
        ),
        responses={
            200: PolymorphicCustomFieldRegistrySerializer(
                field_type_registry, FieldSerializer
            ),
            400: get_error_schema(
                [
                    "ERROR_USER_NOT_IN_GROUP",
                    "ERROR_CANNOT_CHANGE_FIELD_TYPE",
                    "ERROR_REQUEST_BODY_VALIDATION",
                ]
            ),
            404: get_error_schema(["ERROR_FIELD_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            FieldDoesNotExist: ERROR_FIELD_DOES_NOT_EXIST,
            UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
            CannotChangeFieldType: ERROR_CANNOT_CHANGE_FIELD_TYPE,
        }
    )
    def patch(self, request, field_id):
        """Updates the field if the user belongs to the group."""

        field = (
            FieldHandler()
            .get_field(field_id, base_queryset=Field.objects.select_for_update())
            .specific
        )
        type_name = type_from_data_or_registry(request.data, field_type_registry, field)
        field_type = field_type_registry.get(type_name)
        data = validate_data_custom_fields(
            type_name,
            field_type_registry,
            request.data,
            base_serializer_class=UpdateFieldSerializer,
        )

        # Because each field type can raise custom exceptions at while updating the
        # field we need to be able to map those to the correct API exceptions which are
        # defined in the type.
        with field_type.map_api_exceptions():
            field = FieldHandler().update_field(request.user, field, type_name, **data)

        serializer = field_type_registry.get_serializer(field, FieldSerializer)
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="field_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="Deletes the field related to the provided value.",
            )
        ],
        tags=["Database table fields"],
        operation_id="delete_database_table_field",
        description=(
            "Deletes the existing field if the authorized user has access to the "
            "related database's group. Note that all the related data to that field "
            "is also deleted. Primary fields cannot be deleted because their value "
            "represents the row."
        ),
        responses={
            204: None,
            400: get_error_schema(
                ["ERROR_USER_NOT_IN_GROUP", "ERROR_CANNOT_DELETE_PRIMARY_FIELD"]
            ),
            404: get_error_schema(["ERROR_FIELD_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            FieldDoesNotExist: ERROR_FIELD_DOES_NOT_EXIST,
            UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
            CannotDeletePrimaryField: ERROR_CANNOT_DELETE_PRIMARY_FIELD,
        }
    )
    def delete(self, request, field_id):
        """Deletes an existing field if the user belongs to the group."""

        field = FieldHandler().get_field(field_id)
        FieldHandler().delete_field(request.user, field)

        return Response(status=204)
