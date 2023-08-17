from loguru import logger
from rest_framework import serializers

from baserow.contrib.builder.models import Builder
from baserow.contrib.builder.theme.registries import theme_config_block_registry


def serialize_builder_theme(builder: Builder) -> dict:
    """
    A helper function that serializes all theme properties of the provided builder.

    :param builder: The builder that must be serialized.
    :return: The serialized theme properties.
    """

    theme = {}

    for theme_config_block in theme_config_block_registry.get_all():
        serializer_class = theme_config_block.get_serializer_class()
        serializer = serializer_class(
            getattr(builder, theme_config_block.related_name_in_builder_model),
            source=theme_config_block.related_name_in_builder_model,
        )
        theme.update(**serializer.data)

    return theme


def get_combined_theme_config_blocks_serializer_class() -> serializers.Serializer:
    """
    This helper function generates one single serializer that contains all the fields
    of all the theme config blocks. The API always communicates all theme properties
    flat in one single object.

    :return: The generated serializer.
    """

    if hasattr(get_combined_theme_config_blocks_serializer_class, "cache"):
        return get_combined_theme_config_blocks_serializer_class.cached_class

    if len(theme_config_block_registry.registry.values()) == 0:
        logger.warning(
            "The theme config block types appear to be empty. This module is probably "
            "imported before the theme config blocks have been registered."
        )

    attrs = {}

    for theme_config_block in theme_config_block_registry.get_all():
        serializer = theme_config_block.get_serializer_class()
        serializer_fields = serializer().get_fields()

        for name, field in serializer_fields.items():
            attrs[name] = field

    class Meta:
        meta_ref_name = "combined_theme_config_blocks_serializer"

    attrs["Meta"] = Meta

    class_object = type(
        "CombinedThemeConfigBlocksSerializer", (serializers.Serializer,), attrs
    )

    get_combined_theme_config_blocks_serializer_class.cached_class = class_object
    return class_object


CombinedThemeConfigBlocksSerializer = (
    get_combined_theme_config_blocks_serializer_class()
)
