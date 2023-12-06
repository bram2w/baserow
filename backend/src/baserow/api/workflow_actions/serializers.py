from abc import abstractmethod

from rest_framework import serializers

from baserow.core.workflow_actions.models import WorkflowAction


class WorkflowActionSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField(
        help_text="The type of the workflow action"
    )

    class Meta:
        model = WorkflowAction
        fields = ("id", "order", "type")

        extra_kwargs = {
            "id": {"read_only": True},
        }

    @abstractmethod
    def get_type(self, instance: WorkflowAction):
        pass
