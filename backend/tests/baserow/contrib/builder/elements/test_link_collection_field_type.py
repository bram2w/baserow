from baserow.contrib.builder.elements.collection_field_types import (
    LinkCollectionFieldType,
)
from baserow.contrib.builder.elements.receivers import (
    page_deleted_update_link_collection_fields,
)
from baserow.contrib.builder.elements.registries import collection_field_type_registry
from baserow.contrib.builder.pages.signals import page_deleted
from baserow.core.exceptions import InstanceTypeDoesNotExist


def test_registering_link_collection_field_type_connects_to_page_deleted_signal():
    try:
        collection_field_type_registry.get(LinkCollectionFieldType.type)
    except InstanceTypeDoesNotExist:
        collection_field_type_registry.register(LinkCollectionFieldType.type)
    registered_handlers = [receiver[1]() for receiver in page_deleted.receivers]
    assert page_deleted_update_link_collection_fields in registered_handlers


def test_unregistering_link_collection_field_type_disconnects_from_page_deleted_signal():
    collection_field_type_registry.unregister(LinkCollectionFieldType.type)
    registered_handlers = [receiver[1]() for receiver in page_deleted.receivers]
    assert page_deleted_update_link_collection_fields not in registered_handlers
