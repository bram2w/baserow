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
