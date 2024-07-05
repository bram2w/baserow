from abc import ABC
from typing import Type, TypeVar

from django.db.models import QuerySet

from baserow.core.registry import (
    CustomFieldsInstanceMixin,
    CustomFieldsRegistryMixin,
    EasyImportExportMixin,
    Instance,
    Registry,
)
from baserow.core.utils import extract_allowed

from .types import ThemeConfigBlockSubClass


class ThemeConfigBlockType(
    Instance,
    EasyImportExportMixin,
    CustomFieldsInstanceMixin,
    ABC,
):
    """
    A theme config block type can be used to add additional theme properties to a
    builder application.
    """

    model_class: Type[ThemeConfigBlockSubClass]
    """
    Deliberately not using the `ModelInstanceMixin` because the models are not
    polymorphic.
    """

    parent_property_name = "builder"

    def get_property_names(self):
        """
        We want all properties here to make it easier.
        """

        return [
            f.name
            for f in self.model_class._meta.get_fields()
            if f.name not in ["builder", "id"]
        ]

    @property
    def allowed_fields(self):
        return [
            f.name
            for f in self.model_class._meta.get_fields()
            if f.name not in ["id", "builder"]
        ]

    @property
    def serializer_field_names(self):
        return self.allowed_fields

    @property
    def related_name_in_builder_model(self) -> str:
        """
        This is the related name of the model, which automatically get a relationship
        if the `model_class` extends the abstract `ThemeConfigBlock` model.
        """

        return self.model_class.__name__.lower()

    def update_properties(
        self, builder, **kwargs: dict
    ) -> Type[ThemeConfigBlockSubClass]:
        """
        Updates the allowed theme properties for the provided builder object.

        :param builder: The builder of which the theme properties must be updated.
        :param kwargs: The properties that must be updated.
        :return: The updated instance.
        """

        instance = getattr(builder, self.related_name_in_builder_model)
        allowed_values = extract_allowed(kwargs, self.allowed_fields)

        for key, value in allowed_values.items():
            setattr(instance, key, value)

        instance.save()

        setattr(builder, self.related_name_in_builder_model, instance)

        return instance


ThemeConfigBlockTypeSubClass = TypeVar(
    "ThemeConfigBlockTypeSubClass", bound=ThemeConfigBlockType
)


class ThemeConfigBlockRegistry(
    Registry[ThemeConfigBlockTypeSubClass],
    CustomFieldsRegistryMixin,
):
    """
    Contains all registered theme config blocks.
    """

    name = "theme_config_block"

    def enhance_list_builder_queryset(self, queryset: QuerySet) -> QuerySet:
        """
        Enhances the list builder application queryset by applying a `select_related`
        for of every registered theme config block. This is needed to join all the
        related theme data in the query to avoid N queries.

        :param queryset: The queryset that lists the builder applications.
        :return: The enhanced queryset.
        """

        for theme_config_block in self.get_all():
            related_name = theme_config_block.related_name_in_builder_model
            queryset = queryset.select_related(related_name)
        return queryset


theme_config_block_registry = ThemeConfigBlockRegistry()
