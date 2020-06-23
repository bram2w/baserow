from rest_framework import serializers


def get_example_pagination_serializer_class(results_serializer_class):
    """
    Generates a pagination like response serializer that has the provided serializer
    class as results. It is only used for example purposes in combination with the
    openapi documentation.

    :param results_serializer_class: The serializer class that needs to be added as
        results.
    :type results_serializer_class: Serializer
    :return: The generated pagination serializer.
    :rtype: Serializer
    """

    return type(
        'PaginationSerializer' + results_serializer_class.__name__,
        (serializers.Serializer,),
        {
            'count': serializers.IntegerField(help_text='The total amount of results.'),
            'next': serializers.URLField(
                allow_blank=True,
                allow_null=True,
                help_text='URL to the next page.'
            ),
            'previous': serializers.URLField(
                allow_blank=True,
                allow_null=True,
                help_text='URL to the previous page.'
            ),
            'results': results_serializer_class(many=True)
        }
    )
