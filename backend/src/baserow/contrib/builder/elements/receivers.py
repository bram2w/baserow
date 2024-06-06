from django.db.models import F, Func, Value

from baserow.contrib.builder.elements.collection_field_types import (
    LinkCollectionFieldType,
)
from baserow.contrib.builder.elements.models import CollectionField
from baserow.contrib.builder.pages.signals import page_deleted


def page_deleted_update_link_collection_fields(sender, page_id: int, **kwargs):
    """
    When a page is deleted, find all `CollectionField` of `type=link`
    that point to it and reset their `navigate_to_page_id` to `None`.
    """

    CollectionField.objects.filter(type=LinkCollectionFieldType.type).filter(
        config__navigate_to_page_id=page_id
    ).update(
        config=Func(
            F("config"),
            Value(["navigate_to_page_id"]),
            Value("null"),
            function="jsonb_set",
        )
    )


def connect_link_collection_field_type_to_page_delete_signal():
    """
    When LinkCollectionFieldType is registered, this is called so that the page_deleted
    signal is connected to the `page_deleted_update_link_collection_fields` receiver.
    This is so that we only execute the handler if the LinkCollectionFieldType is used.
    """

    page_deleted.connect(page_deleted_update_link_collection_fields)


def disconnect_link_collection_field_type_from_page_delete_signal():
    """
    The opposite of `connect_link_collection_field_type_to_page_delete_signal`, this
    will disconnect the `page_deleted` signal from the receiver.
    """

    page_deleted.disconnect(page_deleted_update_link_collection_fields)
