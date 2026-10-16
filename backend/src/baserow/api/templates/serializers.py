from django.conf import settings

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from baserow.core.models import Template, TemplateCategory
from baserow.core.user_templates.constants import UserTemplateState
from baserow.core.user_templates.handler import UserTemplateHandler


class ListRequestQueryParamSerializer(serializers.Serializer):
    search = serializers.CharField(required=False)


class TemplateSerializer(serializers.ModelSerializer):
    is_default = serializers.SerializerMethodField(
        help_text="Indicates if the template must be selected by default. The "
        "web-frontend automatically selects the first `is_default` template "
        "that it can find."
    )

    class Meta:
        model = Template
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "icon",
            "keywords",
            "workspace_id",
            "is_default",
            "open_application",
        )

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


class UserTemplateSerializer(serializers.ModelSerializer):
    categories = TemplateCategorySerializer(read_only=True, many=True)
    state = serializers.SerializerMethodField(
        help_text="The state of the template as shown to its author."
    )
    reason = serializers.SerializerMethodField(
        help_text="Why the template was rejected or blocked, if given."
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
            "workspace_id",
            "open_application",
            "categories",
            "state",
            "reason",
            "created_on",
            "updated_on",
        )

    @extend_schema_field(serializers.ChoiceField(choices=UserTemplateState.choices))
    def get_state(self, instance):
        state, _ = UserTemplateHandler().get_template_state(instance)
        return state

    @extend_schema_field(OpenApiTypes.STR)
    def get_reason(self, instance):
        _, reason = UserTemplateHandler().get_template_state(instance)
        return reason
