from django.db import transaction
from drf_spectacular.openapi import OpenApiParameter, OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import permission_classes as method_permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from baserow.api.decorators import validate_body_custom_fields, map_exceptions
from baserow.api.errors import ERROR_USER_NOT_IN_GROUP
from baserow.api.schemas import get_error_schema
from baserow.api.trash.errors import ERROR_CANNOT_DELETE_ALREADY_DELETED_ITEM
from baserow.api.utils import DiscriminatorCustomFieldsMappingSerializer
from baserow.api.utils import validate_data_custom_fields, type_from_data_or_registry
from baserow.contrib.database.api.fields.errors import (
    ERROR_CANNOT_DELETE_PRIMARY_FIELD,
    ERROR_CANNOT_CHANGE_FIELD_TYPE,
    ERROR_FIELD_DOES_NOT_EXIST,
    ERROR_MAX_FIELD_COUNT_EXCEEDED,
    ERROR_RESERVED_BASEROW_FIELD_NAME,
    ERROR_FIELD_WITH_SAME_NAME_ALREADY_EXISTS,
    ERROR_INVALID_BASEROW_FIELD_NAME,
    ERROR_FIELD_SELF_REFERENCE,
    ERROR_FIELD_CIRCULAR_REFERENCE,
)
from baserow.contrib.database.api.tables.errors import ERROR_TABLE_DOES_NOT_EXIST
from baserow.contrib.database.api.tokens.authentications import TokenAuthentication
from baserow.contrib.database.api.tokens.errors import ERROR_NO_PERMISSION_TO_TABLE
from baserow.contrib.database.fields.exceptions import (
    CannotDeletePrimaryField,
    CannotChangeFieldType,
    FieldDoesNotExist,
    MaxFieldLimitExceeded,
    ReservedBaserowFieldNameException,
    FieldWithSameNameAlreadyExists,
    InvalidBaserowFieldName,
)
from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.fields.models import Field
from baserow.contrib.database.fields.registries import field_type_registry
from baserow.contrib.database.table.exceptions import TableDoesNotExist
from baserow.contrib.database.table.handler import TableHandler
from baserow.contrib.database.tokens.exceptions import NoPermissionToTable
from baserow.contrib.database.tokens.handler import TokenHandler
from baserow.core.exceptions import UserNotInGroup
from baserow.core.trash.exceptions import CannotDeleteAlreadyDeletedItem
from .serializers import (
    FieldSerializer,
    CreateFieldSerializer,
    UpdateFieldSerializer,
    FieldSerializerWithRelatedFields,
    RelatedFieldsSerializer,
)
from baserow.contrib.database.fields.dependencies.exceptions import (
    SelfReferenceFieldDependencyError,
    CircularFieldDependencyError,
)


class FieldsView(APIView):
    authentication_classes = APIView.authentication_classes + [TokenAuthentication]
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
            200: DiscriminatorCustomFieldsMappingSerializer(
                field_type_registry, FieldSerializer, many=True
            ),
            400: get_error_schema(["ERROR_USER_NOT_IN_GROUP"]),
            401: get_error_schema(["ERROR_NO_PERMISSION_TO_TABLE"]),
            404: get_error_schema(["ERROR_TABLE_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            TableDoesNotExist: ERROR_TABLE_DOES_NOT_EXIST,
            UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
            NoPermissionToTable: ERROR_NO_PERMISSION_TO_TABLE,
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

        TokenHandler().check_table_permissions(
            request, ["read", "create", "update"], table, False
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
            "If creating the field causes other fields to change then the specific"
            "instances of those fields will be included in the related fields "
            "response key."
        ),
        request=DiscriminatorCustomFieldsMappingSerializer(
            field_type_registry, CreateFieldSerializer
        ),
        responses={
            200: DiscriminatorCustomFieldsMappingSerializer(
                field_type_registry, FieldSerializerWithRelatedFields
            ),
            400: get_error_schema(
                [
                    "ERROR_USER_NOT_IN_GROUP",
                    "ERROR_REQUEST_BODY_VALIDATION",
                    "ERROR_MAX_FIELD_COUNT_EXCEEDED",
                    "ERROR_RESERVED_BASEROW_FIELD_NAME",
                    "ERROR_FIELD_WITH_SAME_NAME_ALREADY_EXISTS",
                    "ERROR_INVALID_BASEROW_FIELD_NAME",
                    "ERROR_FIELD_SELF_REFERENCE",
                    "ERROR_FIELD_CIRCULAR_REFERENCE",
                ]
            ),
            401: get_error_schema(["ERROR_NO_PERMISSION_TO_TABLE"]),
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
            MaxFieldLimitExceeded: ERROR_MAX_FIELD_COUNT_EXCEEDED,
            NoPermissionToTable: ERROR_NO_PERMISSION_TO_TABLE,
            FieldWithSameNameAlreadyExists: ERROR_FIELD_WITH_SAME_NAME_ALREADY_EXISTS,
            ReservedBaserowFieldNameException: ERROR_RESERVED_BASEROW_FIELD_NAME,
            InvalidBaserowFieldName: ERROR_INVALID_BASEROW_FIELD_NAME,
            SelfReferenceFieldDependencyError: ERROR_FIELD_SELF_REFERENCE,
            CircularFieldDependencyError: ERROR_FIELD_CIRCULAR_REFERENCE,
        }
    )
    def post(self, request, data, table_id):
        """Creates a new field for a table."""

        type_name = data.pop("type")
        field_type = field_type_registry.get(type_name)
        table = TableHandler().get_table(table_id)
        table.database.group.has_user(request.user, raise_error=True)

        # field_create permission doesn't exists, so any call of this endpoint with a
        # token will be rejected.
        TokenHandler().check_table_permissions(request, "field_create", table, False)

        # Because each field type can raise custom exceptions while creating the
        # field we need to be able to map those to the correct API exceptions which are
        # defined in the type.
        with field_type.map_api_exceptions():
            field, updated_fields = FieldHandler().create_field(
                request.user, table, type_name, return_updated_fields=True, **data
            )

        serializer = field_type_registry.get_serializer(
            field, FieldSerializerWithRelatedFields, related_fields=updated_fields
        )
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
            "related database's group. Depending on the type different properties "
            "could be returned."
        ),
        responses={
            200: DiscriminatorCustomFieldsMappingSerializer(
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
            "If updated the field causes other fields to change then the specific"
            "instances of those fields will be included in the related fields "
            "response key."
        ),
        request=DiscriminatorCustomFieldsMappingSerializer(
            field_type_registry, UpdateFieldSerializer
        ),
        responses={
            200: DiscriminatorCustomFieldsMappingSerializer(
                field_type_registry, FieldSerializerWithRelatedFields
            ),
            400: get_error_schema(
                [
                    "ERROR_USER_NOT_IN_GROUP",
                    "ERROR_CANNOT_CHANGE_FIELD_TYPE",
                    "ERROR_REQUEST_BODY_VALIDATION",
                    "ERROR_RESERVED_BASEROW_FIELD_NAME",
                    "ERROR_FIELD_WITH_SAME_NAME_ALREADY_EXISTS",
                    "ERROR_INVALID_BASEROW_FIELD_NAME",
                    "ERROR_FIELD_SELF_REFERENCE",
                    "ERROR_FIELD_CIRCULAR_REFERENCE",
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
            FieldWithSameNameAlreadyExists: ERROR_FIELD_WITH_SAME_NAME_ALREADY_EXISTS,
            ReservedBaserowFieldNameException: ERROR_RESERVED_BASEROW_FIELD_NAME,
            InvalidBaserowFieldName: ERROR_INVALID_BASEROW_FIELD_NAME,
            SelfReferenceFieldDependencyError: ERROR_FIELD_SELF_REFERENCE,
            CircularFieldDependencyError: ERROR_FIELD_CIRCULAR_REFERENCE,
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
            field, related_fields = FieldHandler().update_field(
                request.user, field, type_name, return_updated_fields=True, **data
            )

        serializer = field_type_registry.get_serializer(
            field, FieldSerializerWithRelatedFields, related_fields=related_fields
        )
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
            "represents the row. "
            "If deleting the field causes other fields to change then the specific"
            "instances of those fields will be included in the related fields "
            "response key."
        ),
        responses={
            200: RelatedFieldsSerializer,
            400: get_error_schema(
                [
                    "ERROR_USER_NOT_IN_GROUP",
                    "ERROR_CANNOT_DELETE_PRIMARY_FIELD",
                    "ERROR_CANNOT_DELETE_ALREADY_DELETED_ITEM",
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
            CannotDeletePrimaryField: ERROR_CANNOT_DELETE_PRIMARY_FIELD,
            CannotDeleteAlreadyDeletedItem: ERROR_CANNOT_DELETE_ALREADY_DELETED_ITEM,
        }
    )
    def delete(self, request, field_id):
        """Deletes an existing field if the user belongs to the group."""

        field = FieldHandler().get_field(field_id)
        field_type = field_type_registry.get_by_model(field.specific_class)
        with field_type.map_api_exceptions():
            updated_fields = FieldHandler().delete_field(request.user, field)

        return Response(RelatedFieldsSerializer({}, related_fields=updated_fields).data)
