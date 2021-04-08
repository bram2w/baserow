from rest_framework import serializers

from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes

from django.conf import settings

from baserow.core.models import TemplateCategory, Template


class TemplateSerializer(serializers.ModelSerializer):
    is_default = serializers.SerializerMethodField(
        help_text='Indicates if the template must be selected by default. The '
                  'web-frontend automatically selects the first `is_default` template '
                  'that it can find.'
    )

    class Meta:
        model = Template
        fields = ('id', 'name', 'icon', 'keywords', 'group_id', 'is_default')

    @extend_schema_field(OpenApiTypes.STR)
    def get_is_default(self, instance):
        return instance.slug == settings.DEFAULT_APPLICATION_TEMPLATE


class TemplateCategoriesSerializer(serializers.ModelSerializer):
    templates = TemplateSerializer(read_only=True, many=True)

    class Meta:
        model = TemplateCategory
        fields = ('id', 'name', 'templates')
