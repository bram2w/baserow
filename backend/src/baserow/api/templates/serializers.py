from django.conf import settings

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from baserow.core.models import Template, TemplateCategory
from baserow.core.user_templates.constants import UserTemplateState
from baserow.core.user_templates.handler import UserTemplateHandler


class ListTemplatesQueryParamSerializer(serializers.Serializer):
    view = serializers.ChoiceField(choices=["flat"], required=False)
    type = serializers.ChoiceField(choices=Template.Type.choices, required=False)
    owned = serializers.BooleanField(required=False, default=False)
    search = serializers.CharField(required=False, allow_blank=True)


class TemplateSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField(
        help_text="Whether it's an official or a user template."
    )
    is_default = serializers.SerializerMethodField(
        help_text="Indicates if the template must be selected by default. The "
        "web-frontend automatically selects the first `is_default` template "
        "that it can find."
    )

    class Meta:
        model = Template
        fields = (
            "id",
            "type",
            "name",
            "slug",
            "description",
            "icon",
            "keywords",
            "workspace_id",
            "is_default",
            "open_application",
        )

    @extend_schema_field(serializers.ChoiceField(choices=Template.Type.choices))
    def get_type(self, instance):
        # A null `type` means official.
        return instance.type or Template.Type.OFFICIAL

    @extend_schema_field(OpenApiTypes.STR)
    def get_is_default(self, instance):
        return instance.slug == settings.DEFAULT_APPLICATION_TEMPLATES[0]


class TemplateCategoriesSerializer(serializers.ModelSerializer):
    templates = TemplateSerializer(read_only=True, many=True)

    class Meta:
        model = TemplateCategory
        fields = ("id", "name", "templates")


class TemplateCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TemplateCategory
        fields = ("id", "name")


class TemplateListItemSerializer(TemplateSerializer):
    """
    A template of the flat list. `state` and `reason` are only shown to the owner
    of a user template, and are null otherwise.
    """

    categories = TemplateCategorySerializer(read_only=True, many=True)
    state = serializers.SerializerMethodField(
        help_text="The state of the template as shown to its owner. Null for "
        "anyone else."
    )
    reason = serializers.SerializerMethodField(
        help_text="Why the template was rejected or blocked, if given. Only shown "
        "to its owner."
    )

    class Meta(TemplateSerializer.Meta):
        fields = TemplateSerializer.Meta.fields + (
            "categories",
            "state",
            "reason",
            "created_on",
            "updated_on",
        )

    def _get_owner_state(self, instance):
        request = self.context.get("request")
        if (
            instance.type != Template.Type.USER
            or request is None
            or instance.owner_id != request.user.id
        ):
            return None, None
        return UserTemplateHandler().get_template_state(instance)

    @extend_schema_field(
        serializers.ChoiceField(choices=UserTemplateState.choices, allow_null=True)
    )
    def get_state(self, instance):
        state, _ = self._get_owner_state(instance)
        return state

    @extend_schema_field(OpenApiTypes.STR)
    def get_reason(self, instance):
        _, reason = self._get_owner_state(instance)
        return reason
