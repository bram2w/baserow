from typing import Any, Dict

from baserow.contrib.builder.models import Builder

from .registries import theme_config_block_registry


class ThemeHandler:
    def update_theme(self, builder: Builder, **kwargs) -> Builder:
        """
        Updates the theme properties of a builder object.

        :param builder: The builder that should be updated.
        :param kwargs: A dict containing the theme properties that must be updated.
        """

        for theme_config_block in theme_config_block_registry.get_all():
            theme_config_block.update_properties(builder, **kwargs)

        return builder

    def export_theme(self, builder: Builder) -> Dict[str, Any]:
        """
        Serializes the theme blocks of the given builder.

        :param builder: The builder instance of the theme to serialize.
        :return: The serialized version of the theme properties.
        """

        # Even though there can be multiple theme config blocks, we still want to
        # export that as a flat object.
        serialized_theme = {}
        for theme_config_block_type in theme_config_block_registry.get_all():
            related_name = theme_config_block_type.related_name_in_builder_model
            theme_config_block = getattr(builder, related_name)
            serialized_theme.update(
                **theme_config_block_type.export_serialized(theme_config_block)
            )
        return serialized_theme

    def import_theme(
        self, builder: Builder, serialized_theme: Dict[str, Any], id_mapping
    ):
        """
        Imports the serialized version of the theme block properties and add the
        properties to the builder.

        :param builder: The builder instance to set the properties.
        :param serialized_theme: The serialized theme properties.
        :param id_mapping: A map of old->new id per data type
            when we have foreign keys that need to be migrated.
        """

        # Exported value is a flat object, each individual theme config block type
        # can extract the correct values from it.
        for theme_config_block_type in theme_config_block_registry.get_all():
            related_name = theme_config_block_type.related_name_in_builder_model
            theme_config_block = theme_config_block_type.import_serialized(
                builder, serialized_theme, id_mapping
            )
            setattr(builder, related_name, theme_config_block)
