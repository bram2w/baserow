from rest_framework import serializers

from baserow.contrib.database.api.views.grid.serializers import (
    GridViewFieldOptionsField,
)


def get_example_pagination_serializer_class(
    results_serializer_class, add_field_options=False
):
    """
    Generates a pagination like response serializer that has the provided serializer
    class as results. It is only used for example purposes in combination with the
    openapi documentation.

    :param results_serializer_class: The serializer class that needs to be added as
        results.
    :param add_field_options: When true will include the field_options field on the
    returned serializer.
    :type results_serializer_class: Serializer
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

    serializer_name = "PaginationSerializer"
    if add_field_options:
        fields["field_options"] = GridViewFieldOptionsField(required=False)
        serializer_name = serializer_name + "WithFieldOptions"

    return type(
        serializer_name + results_serializer_class.__name__,
        (serializers.Serializer,),
        fields,
    )
