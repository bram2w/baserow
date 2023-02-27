from typing import List

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from baserow.api.applications.serializers import ApplicationSerializer
from baserow.contrib.builder.api.pages.serializers import PageSerializer
from baserow.contrib.builder.operations import ListPagesBuilderOperationType
from baserow.contrib.builder.pages.models import Page
from baserow.core.handler import CoreHandler
from baserow.core.models import Application


class BuilderSerializer(ApplicationSerializer):
    pages = serializers.SerializerMethodField(
        help_text="This field is specific to the `builder` application and contains "
        "an array of pages that are in the builder."
    )

    class Meta(ApplicationSerializer.Meta):
        ref_name = "BuilderApplication"
        fields = ApplicationSerializer.Meta.fields + ("pages",)

    @extend_schema_field(PageSerializer(many=True))
    def get_pages(self, instance: Application) -> List:
        """
        Because the instance doesn't know at this point it is a Builder we have to
        select the related pages this way.

        :param instance: The builder application instance.
        :return: A list of serialized pages that belong to this instance.
        """

        pages = Page.objects.filter(builder_id=instance.pk)

        user = self.context.get("user")
        request = self.context.get("request")

        if user is None and hasattr(request, "user"):
            user = request.user

        if user:
            pages = CoreHandler().filter_queryset(
                user,
                ListPagesBuilderOperationType.type,
                pages,
                group=instance.group,
                context=instance,
                allow_if_template=True,
            )

        return PageSerializer(pages, many=True).data
