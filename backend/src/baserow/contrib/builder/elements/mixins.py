from typing import Any, Dict, Generator, List, Optional, Type

from django.db import IntegrityError
from django.db.models import Q, QuerySet
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from rest_framework.exceptions import ValidationError as DRFValidationError

from baserow.api.exceptions import RequestBodyValidationException
from baserow.contrib.builder.api.elements.serializers import (
    CollectionElementPropertyOptionsSerializer,
    CollectionFieldSerializer,
)
from baserow.contrib.builder.data_providers.exceptions import (
    FormDataProviderChunkInvalidException,
)
from baserow.contrib.builder.data_sources.handler import DataSourceHandler
from baserow.contrib.builder.elements.exceptions import (
    CollectionElementPropertyOptionsNotUnique,
)
from baserow.contrib.builder.elements.handler import ElementHandler
from baserow.contrib.builder.elements.models import (
    CollectionElement,
    CollectionElementPropertyOptions,
    CollectionField,
    ContainerElement,
    Element,
    FormElement,
)
from baserow.contrib.builder.elements.registries import (
    collection_field_type_registry,
    element_type_registry,
)
from baserow.contrib.builder.elements.signals import elements_moved
from baserow.contrib.builder.elements.types import CollectionElementSubClass
from baserow.contrib.builder.pages.handler import PageHandler
from baserow.contrib.builder.types import ElementDict
from baserow.core.registry import Instance
from baserow.core.services.dispatch_context import DispatchContext


class ContainerElementTypeMixin:
    # Container element types are imported first.
    import_element_priority = 2

    class SerializedDict(ElementDict):
        pass

    @property
    def child_types_allowed(self) -> List[str]:
        """
        Lets you define which children types can be placed inside the container.

        :return: All the allowed children types
        """

        return [element_type.type for element_type in element_type_registry.get_all()]

    def get_new_place_in_container(
        self, container_element: ContainerElement, places_removed: List[str]
    ) -> Optional[str]:
        """
        Provides an alternative place that elements can move to when places in the
        container are removed.

        :param container_element: The container element that has places removed
        :param places_removed: The places that are being removed
        :return: The new place in the container the elements can be moved to
        """

        return None

    def get_places_in_container_removed(
        self, values: Dict, instance: ContainerElement
    ) -> List[str]:
        """
        This method defines what elements in the container have been removed preceding
        an update of hte container element.

        :param values: The new values that are being set
        :param instance: The current state of the element
        :return: The places in the container that have been removed
        """

        return []

    def apply_order_by_children(self, queryset: QuerySet[Element]) -> QuerySet[Element]:
        """
        Defines the order of the children inside the container.

        :param queryset: The queryset that the order is applied to.
        :return: A queryset with the order applied to
        """

        return queryset.order_by("place_in_container", "order")

    def prepare_value_for_db(
        self, values: Dict, instance: Optional[ContainerElement] = None
    ):
        if instance is not None:  # This is an update operation
            places_removed = self.get_places_in_container_removed(values, instance)

            if len(places_removed) > 0:
                instances_moved = ElementHandler().before_places_in_container_removed(
                    instance, places_removed
                )

                elements_moved.send(self, page=instance.page, elements=instances_moved)

        return super().prepare_value_for_db(values, instance)

    def validate_place_in_container(
        self, place_in_container: str, instance: ContainerElement
    ):
        """
        Validate that the place in container being set on a child is valid.

        :param place_in_container: The place in container being set
        :param instance: The instance of the container element
        :raises DRFValidationError: If the place in container is invalid
        """


class CollectionElementTypeMixin:
    allowed_fields = [
        "data_source",
        "data_source_id",
        "items_per_page",
        "schema_property",
        "button_load_more_label",
    ]
    serializer_field_names = [
        "schema_property",
        "data_source_id",
        "items_per_page",
        "button_load_more_label",
        "property_options",
    ]

    class SerializedDict(ElementDict):
        data_source_id: int
        items_per_page: int
        button_load_more_label: str
        schema_property: str
        property_options: List[Dict]

    def enhance_queryset(self, queryset):
        return queryset.prefetch_related("property_options")

    def after_update(self, instance: CollectionElementSubClass, values):
        """
        After the element has been updated we need to update the property options.

        :param instance: The instance of the element that has been updated.
        :param values: The values that have been updated.
        :return: None
        """

        if "property_options" in values:
            instance.property_options.all().delete()
            try:
                CollectionElementPropertyOptions.objects.bulk_create(
                    [
                        CollectionElementPropertyOptions(
                            **option,
                            element=instance,
                        )
                        for option in values["property_options"]
                    ]
                )
            except IntegrityError as e:
                if "unique constraint" in e.args[0]:
                    raise CollectionElementPropertyOptionsNotUnique()
                raise e

    @property
    def serializer_field_overrides(self):
        from baserow.core.formula.serializers import FormulaSerializerField

        return {
            "data_source_id": serializers.IntegerField(
                allow_null=True,
                default=None,
                help_text=CollectionElement._meta.get_field("data_source").help_text,
                required=False,
            ),
            "schema_property": serializers.CharField(
                allow_null=True,
                default=None,
                help_text=CollectionElement._meta.get_field(
                    "schema_property"
                ).help_text,
                required=False,
            ),
            "items_per_page": serializers.IntegerField(
                default=20,
                help_text=CollectionElement._meta.get_field("items_per_page").help_text,
                required=False,
            ),
            "button_load_more_label": FormulaSerializerField(
                help_text=CollectionElement._meta.get_field(
                    "button_load_more_label"
                ).help_text,
                required=False,
                allow_blank=True,
                default="",
            ),
            "property_options": CollectionElementPropertyOptionsSerializer(
                many=True,
                required=False,
                help_text="The schema property options that can be set for the collection element.",
            ),
        }

    def prepare_value_for_db(
        self, values: Dict, instance: Optional[CollectionElementSubClass] = None
    ):
        if "data_source_id" in values:
            data_source_id = values.pop("data_source_id")
            if data_source_id is not None:
                schema_property = values.get("schema_property", None)
                data_source = DataSourceHandler().get_data_source(data_source_id)
                if data_source.service:
                    service_type = data_source.service.specific.get_type()
                    if service_type.returns_list and schema_property:
                        raise DRFValidationError(
                            "Data sources which return multiple rows cannot be "
                            "used in conjunction with the schema property."
                        )
                else:
                    raise DRFValidationError(
                        f"Data source {data_source_id} is partially "
                        "configured and not ready for use."
                    )

                if instance:
                    current_page = PageHandler().get_page(instance.page_id)
                else:
                    current_page = values["page"]

                if current_page.id != data_source.page_id:
                    raise RequestBodyValidationException(
                        {
                            "data_source_id": [
                                {
                                    "detail": "The provided data source doesn't belong "
                                    "to the same application.",
                                    "code": "invalid_data_source",
                                }
                            ]
                        }
                    )
                values["data_source"] = data_source
            else:
                values["data_source"] = None

        return super().prepare_value_for_db(values, instance)

    def serialize_property(
        self,
        element: CollectionElementSubClass,
        prop_name: str,
        files_zip=None,
        storage=None,
        cache=None,
        **kwargs,
    ):
        """
        You can customize the behavior of the serialization of a property with this
        hook.
        """

        if prop_name == "property_options":
            return [
                {
                    "schema_property": po.schema_property,
                    "filterable": po.filterable,
                    "sortable": po.sortable,
                    "searchable": po.searchable,
                }
                for po in element.property_options.all()
            ]

        return super().serialize_property(
            element,
            prop_name,
            files_zip=files_zip,
            storage=storage,
            cache=cache,
            **kwargs,
        )

    def deserialize_property(
        self,
        prop_name: str,
        value: Any,
        id_mapping: Dict[str, Any],
        files_zip=None,
        storage=None,
        cache=None,
        **kwargs,
    ) -> Any:
        if prop_name == "data_source_id" and value:
            return id_mapping["builder_data_sources"][value]

        return super().deserialize_property(
            prop_name,
            value,
            id_mapping,
            files_zip=files_zip,
            storage=storage,
            cache=cache,
            **kwargs,
        )

    def import_serialized(
        self,
        parent: Any,
        serialized_values: Dict[str, Any],
        id_mapping: Dict[str, Any],
        files_zip=None,
        storage=None,
        cache=None,
        **kwargs,
    ):
        """
        Here we add the data_source_id to the import process to be able to resolve
        current_record formulas migration.
        """

        actual_data_source_id = None
        if (
            serialized_values.get("data_source_id", None)
            and "builder_data_sources" in id_mapping
        ):
            actual_data_source_id = id_mapping["builder_data_sources"][
                serialized_values["data_source_id"]
            ]

        return super().import_serialized(
            parent,
            serialized_values,
            id_mapping,
            files_zip=files_zip,
            storage=storage,
            cache=cache,
            data_source_id=actual_data_source_id,
            **kwargs,
        )

    def create_instance_from_serialized(
        self,
        serialized_values: Dict[str, Any],
        id_mapping,
        files_zip=None,
        storage=None,
        cache=None,
        **kwargs,
    ) -> CollectionElementSubClass:
        """
        Responsible for creating the property options from the serialized values.

        :param serialized_values: The serialized values of the element.
        :param id_mapping: A dictionary containing the mapping of the old and new ids.
        :param files_zip: The zip file containing the files that can be used.
        :param storage: The storage that can be used to store files.
        :param cache: A dictionary that can be used to cache data.
        :param kwargs: Additional keyword arguments.
        :return: The created instance.
        """

        property_options = serialized_values.pop("property_options", [])

        instance = super().create_instance_from_serialized(
            serialized_values,
            id_mapping,
            files_zip=files_zip,
            storage=storage,
            cache=cache,
            **kwargs,
        )

        # Create property options
        options = [CollectionElementPropertyOptions(**po) for po in property_options]
        CollectionElementPropertyOptions.objects.bulk_create(options)

        instance.property_options.add(*options)

        return instance


class CollectionElementWithFieldsTypeMixin(CollectionElementTypeMixin):
    """
    As subclass of `CollectionElementTypeMixin` which extends its functionality to
    include fields. This mixin is used for elements that have fields, like tables.
    """

    @property
    def serializer_field_names(self):
        return super().serializer_field_names + ["fields"]

    @property
    def serializer_field_overrides(self):
        return {
            **super().serializer_field_overrides,
            "fields": CollectionFieldSerializer(many=True, required=False),
        }

    class SerializedDict(CollectionElementTypeMixin.SerializedDict):
        fields: List[Dict]

    def formula_generator(
        self, element: "CollectionElementWithFieldsTypeMixin"
    ) -> Generator[str | Instance, str, None]:
        """
        Generator that iterates over formula fields for LinkCollectionFieldType.

        Some formula fields are in the config JSON field, e.g. page_parameters.
        """

        yield from super().formula_generator(element)

        for collection_field in element.fields.all():
            yield from collection_field.get_type().formula_generator(collection_field)

    def serialize_property(
        self,
        element: CollectionElementSubClass,
        prop_name: str,
        files_zip=None,
        storage=None,
        cache=None,
        **kwargs,
    ):
        """
        You can customize the behavior of the serialization of a property with this
        hook.
        """

        if prop_name == "fields":
            return [
                collection_field_type_registry.get(f.type).export_serialized(f)
                for f in element.fields.all()
            ]

        return super().serialize_property(
            element,
            prop_name,
            files_zip=files_zip,
            storage=storage,
            cache=cache,
            **kwargs,
        )

    def after_create(self, instance: CollectionElementSubClass, values):
        default_fields = [
            {
                "name": _("Column %(count)s") % {"count": 1},
                "type": "text",
                "config": {"value": ""},
            },
            {
                "name": _("Column %(count)s") % {"count": 2},
                "type": "text",
                "config": {"value": ""},
            },
            {
                "name": _("Column %(count)s") % {"count": 3},
                "type": "text",
                "config": {"value": ""},
            },
        ]

        fields = values.get("fields", default_fields)

        created_fields = CollectionField.objects.bulk_create(
            [
                CollectionField(**field, order=index)
                for index, field in enumerate(fields)
            ]
        )
        instance.fields.add(*created_fields)

    def after_update(self, instance: CollectionElementSubClass, values):
        """
        After the element has been updated we need to update the fields.

        :param instance: The instance of the element that has been updated.
        :param values: The values that have been updated.
        :return: None
        """

        if "fields" in values:
            # If the collection element contains fields that are being deleted,
            # we also need to delete the associated workflow actions.
            query = Q()
            for field in values["fields"]:
                if "uid" in field:
                    query |= Q(uid=field["uid"])

            # Call before delete hook of removed fields
            for field in instance.fields.exclude(query):
                field.get_type().before_delete(field)

            # Remove previous fields
            instance.fields.all().delete()

            created_fields = CollectionField.objects.bulk_create(
                [
                    CollectionField(**field, order=index)
                    for index, field in enumerate(values["fields"])
                ]
            )
            instance.fields.add(*created_fields)

        super().after_update(instance, values)

    def before_delete(self, instance: CollectionElementSubClass):
        # Call the before_delete hook of all fields
        for field in instance.fields.all():
            field.get_type().before_delete(field)

        instance.fields.all().delete()

    def create_instance_from_serialized(
        self,
        serialized_values: Dict[str, Any],
        id_mapping,
        files_zip=None,
        storage=None,
        cache=None,
        **kwargs,
    ):
        """Deals with the fields"""

        fields = serialized_values.pop("fields", [])

        instance = super().create_instance_from_serialized(
            serialized_values,
            id_mapping,
            files_zip=files_zip,
            storage=storage,
            cache=cache,
            **kwargs,
        )

        import_field_context = ElementHandler().get_import_context_addition(
            instance.id, id_mapping, cache.get("imported_element_map")
        )

        fields = [
            collection_field_type_registry.get(f["type"]).import_serialized(
                f, id_mapping, **(kwargs | import_field_context)
            )
            for f in fields
        ]

        # Add the field order
        for i, f in enumerate(fields):
            f.order = i

        # Create fields
        created_fields = CollectionField.objects.bulk_create(fields)

        instance.fields.add(*created_fields)

        return instance


class FormElementTypeMixin:
    # Form element types are imported second, after containers.
    import_element_priority = 1

    def is_valid(
        self,
        element: Type[FormElement],
        value: Any,
        dispatch_context: DispatchContext,
    ) -> bool:
        """
        Given an element and form data value, returns whether it's valid.
        Used by `FormDataProviderType` to determine if form data is valid.

        :param element: The element we're trying to use form data in.
        :param value: The form data value, which may be invalid.
        :param dispatch_context: The dispatch context of the request.
        :return: Whether the value is valid or not for this element.
        """

        if element.required and not value:
            raise FormDataProviderChunkInvalidException(
                "The value is required for this element."
            )

        return value
