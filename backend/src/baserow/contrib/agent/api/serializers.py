from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from baserow.api.mixins import UnknownFieldRaisesExceptionSerializerMixin

from ..handler import AgentHandler
from ..models import AgentApplication
from ..types import AgentReadinessState
from ..validators import AGENT_TEXT_MAX_LENGTH


class AgentApplicationSerializer(serializers.ModelSerializer):
    readiness = serializers.SerializerMethodField(
        help_text="Whether the agent's configuration is complete and its model is enabled."
    )

    class Meta:
        model = AgentApplication
        fields = ("name", "readiness")

    @extend_schema_field(
        serializers.ChoiceField(choices=["ready", "incomplete", "unavailable"])
    )
    def get_readiness(self, instance: AgentApplication) -> AgentReadinessState:
        provider_state = self.context.get("ai_provider_states", {}).get(
            instance.workspace_id
        )
        return AgentHandler().get_configuration(
            instance, provider_state=provider_state
        )["state"]


class AgentConfigurationSerializer(serializers.Serializer):
    state = serializers.ChoiceField(choices=["ready", "incomplete", "unavailable"])
    instructions = serializers.CharField(allow_blank=True, trim_whitespace=False)
    provider_type = serializers.CharField(allow_null=True)
    model_identifier = serializers.CharField(allow_null=True)
    errors = serializers.DictField(
        child=serializers.ChoiceField(choices=["required", "unavailable"])
    )


class AgentConfigurationUpdateSerializer(
    UnknownFieldRaisesExceptionSerializerMixin, serializers.ModelSerializer
):
    class Meta:
        model = AgentApplication
        fields = ("instructions", "provider_type", "model_identifier")
        extra_kwargs = {
            "instructions": {
                "max_length": AGENT_TEXT_MAX_LENGTH,
                "trim_whitespace": False,
            },
        }
