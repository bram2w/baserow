from rest_framework import serializers

from baserow.contrib.builder.pages.constants import PAGE_PATH_PARAM_TYPE_CHOICES
from baserow.contrib.builder.pages.models import Page
from baserow.contrib.builder.pages.validators import path_params_validation


class PathParamSerializer(serializers.Serializer):
    param_type = serializers.ChoiceField(choices=PAGE_PATH_PARAM_TYPE_CHOICES)


class PageSerializer(serializers.ModelSerializer):
    path_params = serializers.DictField(
        child=PathParamSerializer(), required=False, validators=[path_params_validation]
    )

    class Meta:
        model = Page
        fields = ("id", "name", "path", "path_params", "order", "builder_id")
        extra_kwargs = {
            "id": {"read_only": True},
            "builder_id": {"read_only": True},
            "order": {"help_text": "Lowest first."},
        }


class CreatePageSerializer(serializers.ModelSerializer):
    path_params = serializers.DictField(
        child=PathParamSerializer(), required=False, validators=[path_params_validation]
    )

    class Meta:
        model = Page
        fields = ("name", "path", "path_params")


class UpdatePageSerializer(serializers.ModelSerializer):
    path_params = serializers.DictField(
        child=PathParamSerializer(), required=False, validators=[path_params_validation]
    )

    class Meta:
        model = Page
        fields = ("name", "path", "path_params")
        extra_kwargs = {"name": {"required": False}, "path": {"required": False}}


class OrderPagesSerializer(serializers.Serializer):
    page_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="The ids of the pages in the order they are supposed to be set in",
    )
