from django.utils.functional import lazy

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from baserow.core.jobs.constants import (
    JOB_CANCELLED,
    JOB_FAILED,
    JOB_FINISHED,
    JOB_PENDING,
)
from baserow.core.jobs.models import Job
from baserow.core.jobs.registries import job_type_registry

VALID_JOB_STATES = [
    JOB_PENDING,
    JOB_FINISHED,
    JOB_FAILED,
    JOB_CANCELLED,
]


class JobSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField(help_text="The type of the job.")

    progress_percentage = serializers.IntegerField(
        source="get_cached_progress_percentage",
        help_text="A percentage indicating how far along the job is. 100 means "
        "that it's finished.",
    )
    state = serializers.CharField(
        source="get_cached_state",
        help_text="Indicates the state of the import job.",
    )

    class Meta:
        model = Job
        fields = (
            "id",
            "type",
            "progress_percentage",
            "state",
            "human_readable_error",
        )
        extra_kwargs = {
            "id": {"read_only": True},
        }

    @extend_schema_field(OpenApiTypes.STR)
    def get_type(self, instance):
        return job_type_registry.get_by_model(instance.specific_class).type


class CreateJobSerializer(serializers.Serializer):
    type = serializers.ChoiceField(
        choices=lazy(job_type_registry.get_types, list)(),
        help_text="The type of the job.",
    )

    class Meta:
        model = Job
        fields = ("user_id", "type")


class ListJobQuerySerializer(serializers.Serializer):
    states = serializers.CharField(required=False)
    job_ids = serializers.CharField(required=False)

    def validate_states(self, value):
        if not value:
            return None

        states = value.split(",")
        for state in states:
            state = state[1:] if state.startswith("!") else state
            if state not in VALID_JOB_STATES:
                raise serializers.ValidationError(
                    f"State {state} is not a valid state."
                    f" Valid states are: {', '.join(VALID_JOB_STATES)}.",
                )
        return states

    def validate_job_ids(self, value):
        if not value:
            return None

        req_job_ids = value.split(",")
        validated_job_ids = []
        for job_id in req_job_ids:
            try:
                validated_job_ids.append(int(job_id))
            except ValueError:
                raise serializers.ValidationError(
                    f"Job id {job_id} is not a valid integer."
                )
        return validated_job_ids
