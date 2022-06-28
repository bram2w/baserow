from django.db import transaction
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from baserow.api.decorators import (
    validate_body_custom_fields,
    map_exceptions,
)
from baserow.api.schemas import get_error_schema
from baserow.core.jobs.exceptions import JobDoesNotExist, MaxJobCountExceeded

from .errors import ERROR_JOB_DOES_NOT_EXIST, ERROR_MAX_JOB_COUNT_EXCEEDED
from baserow.api.utils import DiscriminatorCustomFieldsMappingSerializer

from baserow.core.jobs.registries import job_type_registry
from baserow.core.jobs.handler import JobHandler
from .serializers import JobSerializer, CreateJobSerializer


class JobsView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["Jobs"],
        operation_id="list_job",
        description=(
            "List all existing jobs. Jobs are task executed asynchronously in the "
            "background. You can use the `get_job` endpoint to read the current"
            "progress of a the job."
        ),
        responses={
            200: DiscriminatorCustomFieldsMappingSerializer(
                job_type_registry, JobSerializer, many=True
            ),
        },
    )
    def get(self, request):

        jobs = JobHandler().get_jobs_for_user(request.user)
        data = [
            job_type_registry.get_serializer(job, JobSerializer).data for job in jobs
        ]
        return Response(data)

    @extend_schema(
        tags=["Jobs"],
        operation_id="create_job",
        description=(
            "Creates a new job. This job runs asynchronously in the "
            "background and execute the task specific to the provided type"
            "parameters. The `get_job` can be used to get the current state "
            "of the job."
        ),
        request=DiscriminatorCustomFieldsMappingSerializer(
            job_type_registry,
            CreateJobSerializer,
            request=True,
        ),
        responses={
            200: DiscriminatorCustomFieldsMappingSerializer(
                job_type_registry, JobSerializer
            ),
            400: get_error_schema(
                [
                    "ERROR_USER_NOT_IN_GROUP",
                    "ERROR_REQUEST_BODY_VALIDATION",
                    "ERROR_MAX_JOB_COUNT_EXCEEDED",
                ]
            ),
            404: get_error_schema(["ERROR_GROUP_DOES_NOT_EXIST"]),
        },
    )
    @transaction.atomic
    @validate_body_custom_fields(
        job_type_registry, base_serializer_class=CreateJobSerializer
    )
    @map_exceptions(
        {
            MaxJobCountExceeded: ERROR_MAX_JOB_COUNT_EXCEEDED,
        }
    )
    def post(self, request, data):
        """Creates a new job."""

        type_name = data.pop("type")

        job_type = job_type_registry.get(type_name)

        # Because each type can raise custom exceptions while creating the
        # job we need to be able to map those to the correct API exceptions which are
        # defined in the type.
        with job_type.map_api_exceptions():
            job = JobHandler().create_and_start_job(request.user, type_name, **data)

        serializer = job_type.get_serializer(job, JobSerializer)
        return Response(serializer.data)


class JobView(APIView):
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
        tags=["Jobs"],
        operation_id="get_job",
        description=(
            "Returns the information related to the provided job id. "
            "This endpoint can for example be polled to get the state and progress of "
            "the job in real time."
        ),
        responses={
            200: DiscriminatorCustomFieldsMappingSerializer(
                job_type_registry, JobSerializer
            ),
            404: get_error_schema(["ERROR_JOB_DOES_NOT_EXIST"]),
        },
    )
    @map_exceptions(
        {
            JobDoesNotExist: ERROR_JOB_DOES_NOT_EXIST,
        }
    )
    def get(self, request, job_id):
        """Returns the job related to the provided id."""

        job = JobHandler().get_job(request.user, job_id)
        serializer = job_type_registry.get_serializer(job, JobSerializer)
        return Response(serializer.data)
