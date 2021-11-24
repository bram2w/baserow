from django.db import transaction
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from baserow.api.decorators import map_exceptions, validate_body
from baserow.api.errors import (
    ERROR_USER_NOT_IN_GROUP,
)
from baserow.api.schemas import get_error_schema
from baserow.contrib.database.api.fields.errors import (
    ERROR_FIELD_DOES_NOT_EXIST,
    ERROR_WITH_FORMULA,
    ERROR_FIELD_SELF_REFERENCE,
    ERROR_FIELD_CIRCULAR_REFERENCE,
)
from baserow.contrib.database.api.formula.serializers import (
    TypeFormulaRequestSerializer,
    TypeFormulaResultSerializer,
)
from baserow.contrib.database.fields.dependencies.exceptions import (
    SelfReferenceFieldDependencyError,
    CircularFieldDependencyError,
)
from baserow.contrib.database.fields.dependencies.handler import FieldDependencyHandler
from baserow.contrib.database.fields.exceptions import FieldDoesNotExist
from baserow.contrib.database.fields.field_cache import FieldCache
from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.fields.models import FormulaField
from baserow.contrib.database.formula import BaserowFormulaException
from baserow.core.exceptions import UserNotInGroup


class TypeFormulaView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="field_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The formula field id to type.",
            ),
        ],
        tags=["Database table fields"],
        operation_id="type_formula_field",
        description="Calculates and returns the new type of the specified formula field"
        " if it's formula is changed to the specified value. Does not change the state "
        "of the field in any way.",
        request=TypeFormulaRequestSerializer,
        responses={
            200: TypeFormulaResultSerializer,
            400: get_error_schema(
                [
                    "ERROR_USER_NOT_IN_GROUP",
                    "ERROR_REQUEST_BODY_VALIDATION",
                    "ERROR_WITH_FORMULA",
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
            UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
            FieldDoesNotExist: ERROR_FIELD_DOES_NOT_EXIST,
            BaserowFormulaException: ERROR_WITH_FORMULA,
            SelfReferenceFieldDependencyError: ERROR_FIELD_SELF_REFERENCE,
            CircularFieldDependencyError: ERROR_FIELD_CIRCULAR_REFERENCE,
        }
    )
    @validate_body(TypeFormulaRequestSerializer)
    def post(self, request, field_id, data):
        """
        Given a formula value for a formula field returns the type of that formula
        value.
        """

        field = FieldHandler().get_field(field_id, field_model=FormulaField)
        field.table.database.group.has_user(request.user, raise_error=True)

        field = field.specific
        field.formula = data["formula"]
        field_lookup_cache = FieldCache()
        field.recalculate_internal_fields(field_lookup_cache=field_lookup_cache)
        FieldDependencyHandler.check_for_circular_references(field, field_lookup_cache)

        return Response(TypeFormulaResultSerializer(field).data)
