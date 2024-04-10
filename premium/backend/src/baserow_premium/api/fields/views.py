from django.db import transaction

from baserow_premium.fields.models import AIField
from baserow_premium.fields.tasks import generate_ai_values_for_rows
from baserow_premium.license.features import PREMIUM
from baserow_premium.license.handler import LicenseHandler
from drf_spectacular.openapi import OpenApiParameter, OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from baserow.api.decorators import map_exceptions, validate_body
from baserow.api.errors import ERROR_USER_NOT_IN_GROUP
from baserow.api.generative_ai.errors import (
    ERROR_GENERATIVE_AI_DOES_NOT_EXIST,
    ERROR_MODEL_DOES_NOT_BELONG_TO_TYPE,
)
from baserow.api.schemas import (
    CLIENT_SESSION_ID_SCHEMA_PARAMETER,
    CLIENT_UNDO_REDO_ACTION_GROUP_ID_SCHEMA_PARAMETER,
    get_error_schema,
)
from baserow.contrib.database.api.fields.errors import ERROR_FIELD_DOES_NOT_EXIST
from baserow.contrib.database.api.rows.errors import ERROR_ROW_DOES_NOT_EXIST
from baserow.contrib.database.fields.exceptions import FieldDoesNotExist
from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.fields.operations import ListFieldsOperationType
from baserow.contrib.database.rows.exceptions import RowDoesNotExist
from baserow.contrib.database.rows.handler import RowHandler
from baserow.core.exceptions import UserNotInWorkspace
from baserow.core.generative_ai.exceptions import (
    GenerativeAITypeDoesNotExist,
    ModelDoesNotBelongToType,
)
from baserow.core.generative_ai.registries import generative_ai_model_type_registry
from baserow.core.handler import CoreHandler

from .serializers import GenerateAIFieldValueViewSerializer


class AsyncGenerateAIFieldValuesView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="field_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The field to generate the value for.",
            ),
            CLIENT_SESSION_ID_SCHEMA_PARAMETER,
            CLIENT_UNDO_REDO_ACTION_GROUP_ID_SCHEMA_PARAMETER,
        ],
        tags=["Database table fields"],
        operation_id="generate_table_ai_field_value",
        description=(
            "Endpoint that's used by the AI field to start an sync task that "
            "will update the cell value of the provided row IDs based on the "
            "dynamically constructed prompt configured in the field settings. "
            "\nThis is a **premium** feature."
        ),
        request=None,
        responses={
            200: str,
            400: get_error_schema(
                [
                    "ERROR_GENERATIVE_AI_DOES_NOT_EXIST",
                    "ERROR_MODEL_DOES_NOT_BELONG_TO_TYPE",
                ]
            ),
            404: get_error_schema(
                [
                    "ERROR_FIELD_DOES_NOT_EXIST",
                    "ERROR_ROW_DOES_NOT_EXIST",
                ]
            ),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            FieldDoesNotExist: ERROR_FIELD_DOES_NOT_EXIST,
            RowDoesNotExist: ERROR_ROW_DOES_NOT_EXIST,
            UserNotInWorkspace: ERROR_USER_NOT_IN_GROUP,
            GenerativeAITypeDoesNotExist: ERROR_GENERATIVE_AI_DOES_NOT_EXIST,
            ModelDoesNotBelongToType: ERROR_MODEL_DOES_NOT_BELONG_TO_TYPE,
        }
    )
    @validate_body(GenerateAIFieldValueViewSerializer, return_validated=True)
    def post(self, request: Request, field_id: int, data) -> Response:
        ai_field = FieldHandler().get_field(
            field_id,
            base_queryset=AIField.objects.all().select_related(
                "table__database__workspace"
            ),
        )

        workspace = ai_field.table.database.workspace

        LicenseHandler.raise_if_user_doesnt_have_feature(
            PREMIUM, request.user, workspace
        )

        CoreHandler().check_permissions(
            request.user,
            ListFieldsOperationType.type,
            workspace=workspace,
            context=ai_field.table,
        )

        model = ai_field.table.get_model()
        req_row_ids = data["row_ids"]
        rows = RowHandler().get_rows(model, req_row_ids)
        if len(rows) != len(req_row_ids):
            found_rows_ids = [row.id for row in rows]
            raise RowDoesNotExist(sorted(list(set(req_row_ids) - set(found_rows_ids))))

        generative_ai_model_type = generative_ai_model_type_registry.get(
            ai_field.ai_generative_ai_type
        )
        ai_models = generative_ai_model_type.get_enabled_models(workspace=workspace)

        if ai_field.ai_generative_ai_model not in ai_models:
            raise ModelDoesNotBelongToType(model_name=ai_field.ai_generative_ai_model)

        generate_ai_values_for_rows.delay(request.user.id, ai_field.id, req_row_ids)

        return Response(status=status.HTTP_202_ACCEPTED)
