from drf_spectacular.openapi import AutoSchema as RegularAutoSchema

from .utils import (
    DiscriminatorMappingSerializer,
    DiscriminatorCustomFieldsMappingSerializer,
)


class AutoSchema(RegularAutoSchema):
    def _is_list_view(self, serializer=None):
        """
        Checks if one of the serializer has the `many` property and if it is `True` it
        will force the auto schema to display it a list.
        """

        if (
            isinstance(serializer, DiscriminatorMappingSerializer)
            or isinstance(serializer, DiscriminatorCustomFieldsMappingSerializer)
        ) and serializer.many:
            return True

        return super()._is_list_view(serializer)
