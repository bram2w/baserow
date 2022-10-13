from drf_spectacular.openapi import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from baserow_enterprise.teams.models import Team, TeamSubject

__all__ = ["TeamSerializer", "TeamSubjectSerializer"]


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ("name",)


class TeamResponseSerializer(serializers.ModelSerializer):
    subject_count = serializers.SerializerMethodField(
        help_text="The amount of subjects (e.g. users) that are currently assigned to this team."
    )
    subject_sample = serializers.SerializerMethodField(
        help_text="A sample, by default 10, of the most recent subjects to join this team."
    )

    class Meta:
        model = Team
        fields = (
            "id",
            "name",
            "group",
            "created_on",
            "updated_on",
            "subject_count",
            "subject_sample",
        )
        extra_kwargs = {"id": {"read_only": True}}

    @extend_schema_field(OpenApiTypes.INT)
    def get_subject_count(self, obj):
        return obj.subject_count if hasattr(obj, "subject_count") else 0

    def get_subject_sample(self, obj):
        return obj.subject_sample if hasattr(obj, "subject_sample") else []


class TeamSubjectSerializer(serializers.ModelSerializer):
    subject_type = serializers.CharField()
    subject_id = serializers.IntegerField(required=False, default=None)
    subject_user_email = serializers.EmailField(required=False, default=None)

    class Meta:
        model = TeamSubject
        fields = ("id", "subject_id", "subject_user_email", "subject_type")
        extra_kwargs = {"id": {"read_only": True}}


class TeamSubjectResponseSerializer(serializers.ModelSerializer):
    subject_type = serializers.SerializerMethodField()

    class Meta:
        model = TeamSubject
        fields = ("id", "subject_id", "subject_type", "team")
        extra_kwargs = {"id": {"read_only": True}}

    def get_subject_type(self, obj: TeamSubject) -> str:
        """
        Returns the TeamSubject's `subject_type` natural key.

        :param obj: The TeamSubject record.
        :return: The subject's content type natural key.
        """

        return obj.subject_type_natural_key
