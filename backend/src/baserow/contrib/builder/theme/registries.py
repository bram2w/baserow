from abc import ABC
from typing import Type, TypeVar

from django.db.models import QuerySet

from baserow.core.registry import (
    CustomFieldsInstanceMixin,
    CustomFieldsRegistryMixin,
    ImportExportMixin,
    Instance,
    Registry,
)
from baserow.core.utils import extract_allowed

from .models import ThemeConfigBlock
from .types import ThemeConfigBlockSubClass


class ThemeConfigBlockType(
    Instance,
    ImportExportMixin[ThemeConfigBlock],
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

    @property
    def related_name_in_builder_model(self) -> str:
        """
        This is the related name of the model, which automatically get a relationship
        if the `model_class` extends the abstract `ThemeConfigBlock` model.
        """

        return self.model_class.__name__.lower()

    def export_serialized(self, instance):
        return {field: getattr(instance, field) for field in self.allowed_fields}

    def import_serialized(self, parent, serialized_values, id_mapping):
        allowed_values = extract_allowed(serialized_values, self.allowed_fields)
        theme_config_block = self.model_class(builder=parent, **allowed_values)
        theme_config_block.save()
        return theme_config_block

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
