from rest_framework import serializers

from baserow.contrib.builder.pages.models import Page


class PageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = ("id", "name", "order", "builder_id")
        extra_kwargs = {
            "id": {"read_only": True},
            "builder_id": {"read_only": True},
            "order": {"help_text": "Lowest first."},
        }


class CreatePageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = ("name",)


class OrderPagesSerializer(serializers.Serializer):
    page_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="The ids of the pages in the order they are supposed to be set in",
    )
