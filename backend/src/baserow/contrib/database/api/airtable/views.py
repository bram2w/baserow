from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from django.db import transaction

from baserow.api.schemas import get_error_schema
from baserow.api.decorators import map_exceptions, validate_body
from baserow.api.errors import ERROR_USER_NOT_IN_GROUP, ERROR_GROUP_DOES_NOT_EXIST
from baserow.core.exceptions import UserNotInGroup, GroupDoesNotExist
from baserow.core.handler import CoreHandler
from baserow.contrib.database.airtable.exceptions import (
    AirtableImportJobDoesNotExist,
    AirtableImportJobAlreadyRunning,
)
from baserow.contrib.database.airtable.handler import AirtableHandler
from baserow.contrib.database.airtable.utils import extract_share_id_from_url

from .serializers import AirtableImportJobSerializer, CreateAirtableImportJobSerializer
from .errors import (
    ERROR_AIRTABLE_IMPORT_JOB_DOES_NOT_EXIST,
    ERROR_AIRTABLE_JOB_ALREADY_RUNNING,
)


class CreateAirtableImportJobView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["Database airtable import"],
        operation_id="create_airtable_import_job",
        description=(
            "Creates a new Airtable import job. This job runs asynchronously in the "
            "background and imports the Airtable base related to the provided "
            "parameters. The `get_airtable_import_job` can be used to get the state "
            "of the import job."
        ),
        request=CreateAirtableImportJobSerializer,
        responses={
            200: AirtableImportJobSerializer,
            400: get_error_schema(
                ["ERROR_USER_NOT_IN_GROUP", "ERROR_AIRTABLE_JOB_ALREADY_RUNNING"]
            ),
            404: get_error_schema(["ERROR_GROUP_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            GroupDoesNotExist: ERROR_GROUP_DOES_NOT_EXIST,
            UserNotInGroup: ERROR_USER_NOT_IN_GROUP,
            AirtableImportJobAlreadyRunning: ERROR_AIRTABLE_JOB_ALREADY_RUNNING,
        }
    )
    @validate_body(CreateAirtableImportJobSerializer)
    @transaction.atomic
    def post(self, request, data):
        group = CoreHandler().get_group(data["group_id"])
        airtable_share_id = extract_share_id_from_url(data["airtable_share_url"])
        job = AirtableHandler.create_and_start_airtable_import_job(
            request.user,
            group,
            airtable_share_id,
            timezone=data.get("timezone"),
        )
        return Response(AirtableImportJobSerializer(job).data)


class AirtableImportJobView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="job_id",
                location=OpenApiParameter.PATH,
                type=OpenApiTypes.INT,
                description="The job id to lookup information about.",
            )
        ],
        tags=["Database airtable import"],
        operation_id="get_airtable_import_job",
        description=(
            "Returns the information related to the provided Airtable import job id. "
            "This endpoint can for example be polled to get the state of the import "
            "job in real time."
        ),
        responses={
            200: AirtableImportJobSerializer,
            404: get_error_schema(["ERROR_AIRTABLE_IMPORT_JOB_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            AirtableImportJobDoesNotExist: ERROR_AIRTABLE_IMPORT_JOB_DOES_NOT_EXIST,
        }
    )
    def get(self, request, job_id):
        job = AirtableHandler.get_airtable_import_job(request.user, job_id)
        return Response(AirtableImportJobSerializer(job).data)
