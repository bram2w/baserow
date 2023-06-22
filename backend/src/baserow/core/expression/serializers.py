from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers


@extend_schema_field(OpenApiTypes.STR)
class ExpressionSerializer(serializers.CharField):
    """
    The expression field can be used to ensure the given data is an expression.
    """
