from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type, TypeVar

from baserow.core.registry import (
    CustomFieldsInstanceMixin,
    CustomFieldsRegistryMixin,
    EasyImportExportMixin,
    Instance,
    ModelInstanceMixin,
    ModelRegistryMixin,
    Registry,
)

from .models import Element
from .types import ElementDictSubClass, ElementSubClass


class ElementType(
    Instance,
    ModelInstanceMixin[ElementSubClass],
    EasyImportExportMixin[ElementSubClass],
    CustomFieldsInstanceMixin,
    ABC,
):
    """Element type"""

    SerializedDict: Type[ElementDictSubClass]
    parent_property_name = "page"
    id_mapping_name = "builder_page_elements"

    def prepare_value_for_db(self, values: Dict, instance: Optional[Element] = None):
        """
        This function allows you to hook into the moment an element is created or
        updated. If the element is updated `instance` will be defined, and you can use
        `instance` to extract any context data that might be required for the
        implementation of this hook.

        :param values: The values that are being updated
        :param instance: (optional) The existing instance that is being updated
        :return:
        """

        from baserow.contrib.builder.elements.handler import ElementHandler

        parent_element_id = values.get(
            "parent_element_id", getattr(instance, "parent_element_id", None)
        )
        place_in_container = values.get("place_in_container", None)

        if parent_element_id is not None and place_in_container is not None:
            parent_element = ElementHandler().get_element(parent_element_id)
            parent_element_type = element_type_registry.get_by_model(parent_element)
            parent_element_type.validate_place_in_container(
                place_in_container, parent_element
            )

        return values

    def after_create(self, instance: ElementSubClass, values: Dict):
        """
        This hook is called right after the element has been created.

        :param instance: The created element instance.
        :param values: The values that were passed when creating the field
            instance.
        """

    def after_update(self, instance: ElementSubClass, values: Dict):
        """
        This hook is called right after the element has been updated.

        :param instance: The updated element instance.
        :param values: The values that were passed when creating the field
            instance.
        """

    def before_delete(self, instance: ElementSubClass):
        """
        This hook is called just before the element will be deleted.

        :param instance: The to be deleted element instance.
        """

    def serialize_property(self, element: Element, prop_name: str):
        """
        You can customize the behavior of the serialization of a property with this
        hook.
        """

        if prop_name == "order":
            return str(element.order)

        return super().serialize_property(element, prop_name)

    def deserialize_property(
        self, prop_name: str, value: Any, id_mapping: Dict[str, Any]
    ) -> Any:
        """
        This hooks allow to customize the deserialization of a property.

        :param prop_name: the name of the property being transformed.
        :param value: the value of this property.
        :param id_mapping: the id mapping dict.
        :return: the deserialized version for this property.
        """

        if prop_name == "parent_element_id":
            return id_mapping["builder_page_elements"].get(
                value,
                value,
            )

        return value

    @abstractmethod
    def get_sample_params(self) -> Dict[str, Any]:
        """
        Returns a sample of params for this type. This can be used to tests the element
        for instance.
        """


ElementTypeSubClass = TypeVar("ElementTypeSubClass", bound=ElementType)


class ElementTypeRegistry(
    Registry[ElementTypeSubClass],
    ModelRegistryMixin[ElementSubClass, ElementTypeSubClass],
    CustomFieldsRegistryMixin,
):
    """
    Contains all registered element types.
    """

    name = "element_type"


element_type_registry = ElementTypeRegistry()
