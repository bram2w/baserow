from rest_framework import serializers


def get_example_pagination_serializer_class(
    results_serializer_class,
    additional_fields=None,
    serializer_name=None,
):
    """
    Generates a pagination like response serializer that has the provided serializer
    class as results. It is only used for example purposes in combination with the
    openapi documentation.

    :param results_serializer_class: The serializer class that needs to be added as
        results.
    :type results_serializer_class: Serializer
    :param additional_fields: A dict containing additional fields that must be added
        to the serializer. The fields are going to be placed at the root of the
        serializer.
    :type additional_fields: dict
    :param serializer_name: The class name of the serializer. Generated serializer
        should be unique because serializer with the same class name are reused.
    :type serializer_name: str
    :return: The generated pagination serializer.
    :rtype: Serializer
    """

    fields = {
        "count": serializers.IntegerField(help_text="The total amount of results."),
        "next": serializers.URLField(
            allow_blank=True, allow_null=True, help_text="URL to the next page."
        ),
        "previous": serializers.URLField(
            allow_blank=True, allow_null=True, help_text="URL to the previous page."
        ),
        "results": results_serializer_class(many=True),
    }

    if additional_fields:
        fields.update(**additional_fields)

    if not serializer_name:
        serializer_name = "PaginationSerializer"

    return type(
        serializer_name + results_serializer_class.__name__,
        (serializers.Serializer,),
        fields,
    )
