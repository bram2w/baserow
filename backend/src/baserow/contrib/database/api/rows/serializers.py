import logging

from rest_framework import serializers

from baserow.api.serializers import get_example_pagination_serializer_class
from baserow.api.utils import get_serializer_class
from baserow.contrib.database.fields.registries import field_type_registry
from baserow.contrib.database.rows.registries import row_metadata_registry

logger = logging.getLogger(__name__)


class RowSerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            "id",
            "order",
        )
        extra_kwargs = {"id": {"read_only": True}, "order": {"read_only": True}}


def get_row_serializer_class(
    model,
    base_class=None,
    is_response=False,
    field_ids=None,
    field_names_to_include=None,
    user_field_names=False,
    field_kwargs=None,
):
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
    :param field_ids: If provided only the field ids in the list will be
        included in the serializer. By default all the fields of the model are going
        to be included. Note that the field id must exist in the model in
        order to work.
    :type field_ids: list or None
    :param field_names_to_include: If provided only the field names in the list will be
        included in the serializer. By default all the fields of the model are going
        to be included. Note that the field name must exist in the model in
        order to work.
    :type field_names_to_include: list or None
    :param field_kwargs: A dict containing additional kwargs per field. The key must
        be the field name and the value a dict containing the kwargs.
    :type field_kwargs: dict
    :return: The generated serializer.
    :rtype: ModelSerializer
    """

    if not field_kwargs:
        field_kwargs = {}

    field_objects = model._field_objects
    field_names = []
    field_overrides = {}

    for field in field_objects.values():
        field_id_matches = field_ids is None or (field["field"].id in field_ids)
        field_name_matches = field_names_to_include is None or (
            field["field"].name in field_names_to_include
        )

        if field_id_matches and field_name_matches:
            name = field["field"].name if user_field_names else field["name"]
            extra_kwargs = field_kwargs.get(field["name"], {})

            if field["name"] != name:
                # If we are building a serializer with names which do not match the
                # database column then we have to set the source.
                # We don't always do this if user_field_names is True as a user could
                # have named fields "field_1" etc, in which case if we also set source
                # DRF would crash as it only wants source set if the db column differs.
                extra_kwargs["source"] = field["name"]

            if is_response:
                serializer = field["type"].get_response_serializer_field(
                    field["field"], **extra_kwargs
                )
            else:
                serializer = field["type"].get_serializer_field(
                    field["field"], **extra_kwargs
                )
            field_overrides[name] = serializer
            field_names.append(name)

    return get_serializer_class(model, field_names, field_overrides, base_class)


def get_example_row_serializer_class(add_id=False, user_field_names=False):
    """
    Generates a serializer containing a field for each field type. It is only used for
    example purposes in the openapi documentation.

    :param add_id: Indicates whether the id field should be added. This could for
        example differ for request or response documentation.
    :type add_id: bool
    :param user_field_names: Whether this example serializer help text should indicate
        the fields names can be switched using the `user_field_names` GET parameter.
    :type user_field_names: bool
    :return: Generated serializer containing a field for each field type.
    :rtype: Serializer
    """

    if not hasattr(get_example_row_serializer_class, "cache"):
        get_example_row_serializer_class.cache = {}

    class_name = (
        "ExampleRowResponseSerializer" if add_id else "ExampleRowRequestSerializer"
    )

    if user_field_names:
        class_name += "WithUserFieldNames"

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

    optional_user_field_names_info = ""
    if user_field_names:
        optional_user_field_names_info = (
            " If the GET parameter `user_field_names` is provided then the key will "
            "instead be the actual name of the field."
        )

    for i, field_type in enumerate(field_types):
        instance = field_type.model_class()
        kwargs = {
            "help_text": f"This field represents the `{field_type.type}` field. The "
            f"number in field_{i + 1} is in a normal request or response "
            f"the id of the field.{optional_user_field_names_info}"
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


def get_example_row_metadata_field_serializer():
    """
    Generates a serializer containing a field for each row metadata type which
    represents the metadata for a single row.
    It is only used for example purposes in the openapi documentation.

    :return: Generated serializer for a single rows metadata
    :rtype: Serializer
    """

    metadata_types = row_metadata_registry.get_all()

    if len(metadata_types) == 0:
        return None

    fields = {}
    for metadata_type in metadata_types:
        fields[metadata_type.type] = metadata_type.get_example_serializer_field()

    per_row_serializer = type(
        "RowMetadataSerializer", (serializers.Serializer,), fields
    )()
    return serializers.DictField(
        child=per_row_serializer,
        required=False,
        help_text="An object keyed by row id with a value being an object containing "
        "additional metadata about that row. A row might not have metadata and will "
        "not be present as a key if so.",
    )


example_pagination_row_serializer_class = get_example_pagination_serializer_class(
    get_example_row_serializer_class(True, user_field_names=True)
)


class MoveRowQueryParamsSerializer(serializers.Serializer):
    before_id = serializers.IntegerField(required=False)


class CreateRowQueryParamsSerializer(serializers.Serializer):
    before = serializers.IntegerField(required=False)


class ListRowsQueryParamsSerializer(serializers.Serializer):
    user_field_names = serializers.BooleanField(required=False, default=False)
    search = serializers.CharField(required=False)
    order_by = serializers.CharField(required=False)
    include = serializers.CharField(required=False)
    exclude = serializers.CharField(required=False)
    filter_type = serializers.CharField(required=False, default="")
