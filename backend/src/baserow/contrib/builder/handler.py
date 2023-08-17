from baserow.contrib.builder.models import Builder
from baserow.contrib.builder.theme.registries import theme_config_block_registry
from baserow.core.handler import CoreHandler


class BuilderHandler:
    def get_builder(self, builder_id: int) -> Builder:
        """
        Gets builder instance from database using its ID

        :param builder_id: ID of the builder instance you want to get
        :return: The builder model instance
        """

        theme_config_block_related_names = [
            config_block.related_name_in_builder_model
            for config_block in theme_config_block_registry.get_all()
        ]

        return (
            CoreHandler()
            .get_application(
                builder_id,
                base_queryset=Builder.objects.select_related(
                    "workspace", *theme_config_block_related_names
                ),
            )
            .specific
        )
