from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "baserow.core"

    def ready(self):
        from baserow.core.trash.registries import trash_item_type_registry
        from baserow.core.trash.trash_types import GroupTrashableItemType
        from baserow.core.trash.trash_types import ApplicationTrashableItemType

        trash_item_type_registry.register(GroupTrashableItemType())
        trash_item_type_registry.register(ApplicationTrashableItemType())
