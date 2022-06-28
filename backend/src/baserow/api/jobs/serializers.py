from django.utils.functional import lazy
from rest_framework import serializers
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field

from baserow.core.jobs.models import Job
from baserow.core.jobs.registries import job_type_registry


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
        # It could be that the field related to the instance is already in the context
        # else we can call the specific_class property to find it.
        field = self.context.get("instance_type")

        if not field:
            field = job_type_registry.get_by_model(instance.specific_class)

        return field.type


class CreateJobSerializer(serializers.Serializer):
    type = serializers.ChoiceField(
        choices=lazy(job_type_registry.get_types, list)(),
        help_text="The type of the job.",
    )

    class Meta:
        model = Job
        fields = ("user_id", "type")
