from typing import List

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from baserow.api.integrations.serializers import PolymorphicIntegrationSerializer
from baserow.api.user_sources.serializers import PolymorphicUserSourceSerializer
from baserow.contrib.builder.api.pages.serializers import PageSerializer
from baserow.contrib.builder.api.theme.serializers import (
    CombinedThemeConfigBlocksSerializer,
    serialize_builder_theme,
)
from baserow.contrib.builder.models import Builder
from baserow.contrib.builder.operations import ListPagesBuilderOperationType
from baserow.core.handler import CoreHandler
from baserow.core.integrations.operations import (
    ListIntegrationsApplicationOperationType,
)
from baserow.core.user_sources.operations import ListUserSourcesApplicationOperationType


class BuilderSerializer(serializers.ModelSerializer):
    """
    The builder serializer.

    👉 Mind to update the
    baserow.contrib.builder.api.domains.serializer.PublicBuilderSerializer
    when you update this one.
    """

    pages = serializers.SerializerMethodField(
        help_text="This field is specific to the `builder` application and contains "
        "an array of pages that are in the builder."
    )
    integrations = serializers.SerializerMethodField(
        help_text="The integrations related with this builder."
    )
    user_sources = serializers.SerializerMethodField(
        help_text="The user sources related with this builder."
    )
    theme = serializers.SerializerMethodField(
        help_text="This field is specific to the `builder` application and contains "
        "the theme settings."
    )

    class Meta:
        model = Builder
        ref_name = "BuilderApplication"
        fields = ("id", "name", "pages", "theme", "integrations", "user_sources")

    @extend_schema_field(PageSerializer(many=True))
    def get_pages(self, instance: Builder) -> List:
        """
        Because the instance doesn't know at this point it is a Builder we have to
        select the related pages this way.

        :param instance: The builder application instance.
        :return: A list of serialized pages that belong to this instance.
        """

        pages = instance.page_set.all()

        user = self.context.get("user")
        request = self.context.get("request")

        if user is None and hasattr(request, "user"):
            user = request.user

        if user:
            pages = CoreHandler().filter_queryset(
                user,
                ListPagesBuilderOperationType.type,
                pages,
                workspace=instance.workspace,
                allow_if_template=True,
            )

        return PageSerializer(pages, many=True).data

    @extend_schema_field(PolymorphicIntegrationSerializer(many=True))
    def get_integrations(self, instance: Builder) -> List:
        """
        Returns the integrations related to this builder.

        :param instance: The builder application instance.
        :return: A list of serialized integrations that belong to this instance.
        """

        integrations = instance.integrations.all()

        user = self.context.get("user")
        request = self.context.get("request")

        if user is None and hasattr(request, "user"):
            user = request.user

        if user:
            integrations = CoreHandler().filter_queryset(
                user,
                ListIntegrationsApplicationOperationType.type,
                integrations,
                workspace=instance.workspace,
                allow_if_template=True,
            )

        return PolymorphicIntegrationSerializer(integrations, many=True).data

    @extend_schema_field(PolymorphicUserSourceSerializer(many=True))
    def get_user_sources(self, instance: Builder) -> List:
        """
        Returns the user sources related to this builder.

        :param instance: The builder application instance.
        :return: A list of serialized user sources that belong to this instance.
        """

        user_sources = instance.user_sources.all()

        user = self.context.get("user")
        request = self.context.get("request")

        if user is None and hasattr(request, "user"):
            user = request.user

        if user:
            user_sources = CoreHandler().filter_queryset(
                user,
                ListUserSourcesApplicationOperationType.type,
                user_sources,
                workspace=instance.workspace,
                allow_if_template=True,
            )

        return PolymorphicUserSourceSerializer(user_sources, many=True).data

    @extend_schema_field(CombinedThemeConfigBlocksSerializer())
    def get_theme(self, instance):
        return serialize_builder_theme(instance)
