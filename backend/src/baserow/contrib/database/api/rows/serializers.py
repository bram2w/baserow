import logging

from rest_framework import serializers

from baserow.api.utils import get_serializer_class
from baserow.api.serializers import get_example_pagination_serializer_class
from baserow.core.utils import model_default_values, dict_to_object
from baserow.contrib.database.fields.registries import field_type_registry

logger = logging.getLogger(__name__)


class RowSerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            "id",
            "order",
        )
        extra_kwargs = {"id": {"read_only": True}, "order": {"read_only": True}}


def get_row_serializer_class(model, base_class=None, is_response=False, field_ids=None):
    """
    Generates a Django rest framework model serializer based on the available fields
    that belong to this model. For each table field, used to generate this serializer,
    a serializer field will be added via the `get_serializer_field` method of the field
    type.

    :param model: The model for which to generate a serializer.
    :type model: Model
    :param base_class: The base serializer class that will be extended when
        generating the serializer. By default this is a regular ModelSerializer.
    :type base_class: ModelSerializer
    :param is_response: Indicates if the serializer is going to be used for a response
        instead of handling input data. If that is the case other serializer fields
        might be used depending on the field type.
    :type is_response: bool
    :param field_ids: If provided only the field ids in the list will be included in
        the serializer. By default all the fields of the model are going to be
        included. Note that the field id must exist in the model in order to work.
    :type field_ids: list or None
    :return: The generated serializer.
    :rtype: ModelSerializer
    """

    field_objects = model._field_objects
    field_names = [
        field["name"]
        for field in field_objects.values()
        if field_ids is None or field["field"].id in field_ids
    ]
    field_overrides = {
        field["name"]: field["type"].get_response_serializer_field(field["field"])
        if is_response
        else field["type"].get_serializer_field(field["field"])
        for field in field_objects.values()
        if field_ids is None or field["field"].id in field_ids
    }
    return get_serializer_class(model, field_names, field_overrides, base_class)


def get_example_row_serializer_class(add_id=False):
    """
    Generates a serializer containing a field for each field type. It is only used for
    example purposes in the openapi documentation.

    :param add_id: Indicates whether the id field should be added. This could for
        example differ for request or response documentation.
    :type add_id: bool
    :return: Generated serializer containing a field for each field type.
    :rtype: Serializer
    """

    if not hasattr(get_example_row_serializer_class, "cache"):
        get_example_row_serializer_class.cache = {}

    class_name = (
        "ExampleRowResponseSerializer" if add_id else "ExampleRowRequestSerializer"
    )

    if class_name in get_example_row_serializer_class.cache:
        return get_example_row_serializer_class.cache[class_name]

    fields = {}

    if add_id:
        fields["id"] = serializers.IntegerField(
            read_only=True, help_text="The unique identifier of the row in the table."
        )
        fields["order"] = serializers.DecimalField(
            max_digits=40,
            decimal_places=20,
            required=False,
            help_text="Indicates the position of the row, lowest first and highest "
            "last.",
        )

    field_types = field_type_registry.registry.values()

    if len(field_types) == 0:
        logger.warning(
            "The field types appear to be empty. This module is probably "
            "imported before the fields have been registered."
        )

    for i, field_type in enumerate(field_types):
        # In order to generate a serializer we need a model instance. This method is
        # called before Django has been loaded so it will result in errors when
        # creating an instance. Therefore we create an object containing the default
        # field values of the model. With the object we can generate the example
        # serializer.
        defaults = model_default_values(field_type.model_class)
        instance = dict_to_object(defaults)
        kwargs = {
            "help_text": f"This field represents the `{field_type.type}` field. The "
            f"number in field_{i + 1} is in a normal request or response "
            f"the id of the field. "
            f"{field_type.get_serializer_help_text(instance)}"
        }
        get_field_method = (
            "get_response_serializer_field" if add_id else "get_serializer_field"
        )
        serializer_field = getattr(field_type, get_field_method)(instance, **kwargs)
        fields[f"field_{i + 1}"] = serializer_field

    class_object = type(class_name, (serializers.Serializer,), fields)
    get_example_row_serializer_class.cache[class_name] = class_object

    return class_object


example_pagination_row_serializer_class = get_example_pagination_serializer_class(
    get_example_row_serializer_class(True)
)
example_pagination_row_serializer_class_with_field_options = (
    get_example_pagination_serializer_class(
        get_example_row_serializer_class(True), add_field_options=True
    )
)
