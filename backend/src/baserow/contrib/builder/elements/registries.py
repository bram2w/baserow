from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypedDict, TypeVar, Union

from django.db import models

from rest_framework import serializers

from baserow.core.registry import (
    CustomFieldsInstanceMixin,
    CustomFieldsRegistryMixin,
    EasyImportExportMixin,
    Instance,
    ModelInstanceMixin,
    ModelRegistryMixin,
    Registry,
)

from .models import CollectionField, Element
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


class CollectionFieldType(
    Instance,
    CustomFieldsInstanceMixin,
    ABC,
):
    """Collection element field type"""

    SerializedDict: TypedDict

    model_class = CollectionField

    def serialize_property(self, config: Dict[str, Any], prop_name: str):
        return config[prop_name]

    def export_serialized(self, instance: CollectionField) -> Dict[str, Any]:
        property_names = self.SerializedDict.__annotations__.keys()

        serialized_config = self.SerializedDict(
            **{
                key: self.serialize_property(instance.config, key)
                for key in property_names
            }
        )

        serialized = {
            "name": instance.name,
            "type": instance.type,
            "config": serialized_config,
        }

        return serialized

    def deserialize_property(
        self,
        prop_name: str,
        value: Any,
        id_mapping: Dict[str, Any],
        data_source_id: Optional[int] = None,
    ) -> Any:
        """
        This hooks allow to customize the deserialization of a property.

        :param prop_name: the name of the property being transformed.
        :param value: the value of this property.
        :param id_mapping: the id mapping dict.
        :return: the deserialized version for this property.
        """

        return value

    def create_instance_from_serialized(
        self, serialized_values: Dict[str, Any]
    ) -> CollectionField:
        """
        Create the instance related to the given serialized values.
        Allow to hook into instance creation while still having the serialized values.

        :param serialized_values: the deserialized values.
        :return: the created instance.
        """

        # We don't save the new instance intentionally to be able to bulk create them
        return CollectionField(**serialized_values)

    def import_serialized(
        self,
        serialized_values: Dict[str, Any],
        id_mapping: Dict[str, Any],
        data_source_id: Optional[int] = None,
    ) -> CollectionField:
        """
        Imports the previously exported dict generated by the `export_serialized`
        method.

        An id_mapping for this class is populated during the process.

        :param parent: The parent object of the to be imported values.
        :serialized_values: The dict containing the serialized values.
        :id_mapping: Used to mapped object ids from export to newly created instances.
        :return: The created instance.
        """

        deserialized_config = {}
        for name in self.SerializedDict.__annotations__.keys():
            deserialized_config[name] = self.deserialize_property(
                name,
                serialized_values["config"][name],
                id_mapping,
                data_source_id=data_source_id,
            )

        deserialized_values = {
            "config": deserialized_config,
            "type": serialized_values["type"],
            "name": serialized_values["name"],
        }

        return self.create_instance_from_serialized(deserialized_values)

    def get_serializer(
        self,
        model_instance_or_instances: Union[models.Model, List[models.Model]],
        base_class: Optional[serializers.ModelSerializer] = None,
        context: Optional[Dict[str, Any]] = None,
        request: bool = False,
        **kwargs: Dict[str, Any],
    ) -> serializers.ModelSerializer:
        """
        Returns an instantiated model serializer based on this type field names and
        overrides. The provided model instance will be used instantiate the serializer.

        :param model_instance_or_instances: The instance or a list of instances for
            which the serializer must be generated.
        :param base_class: The base serializer class that must be extended. For example
            common fields could be stored here.
        :param context: Extra context arguments to pass to the serializers context.
        :param request: True if you want the request serializer.
        :param kwargs: The kwargs are used to initialize the serializer class.
        :return: The instantiated generated model serializer.
        """

        if context is None:
            context = {}

        model_instance_or_instances = model_instance_or_instances

        serializer_class = self.get_serializer_class(
            base_class=base_class, request_serializer=request
        )

        return serializer_class(model_instance_or_instances, context=context, **kwargs)


CollectionFieldTypeSubClass = TypeVar(
    "CollectionFieldTypeSubClass", bound=CollectionFieldType
)


class CollectionFieldTypeRegistry(
    Registry[CollectionFieldTypeSubClass],
    CustomFieldsRegistryMixin,
):
    """
    Contains all registered collection field types.
    """

    name = "collection_field_type"


collection_field_type_registry = CollectionFieldTypeRegistry()
