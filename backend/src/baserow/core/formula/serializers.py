from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from baserow.formula.parser.exceptions import BaserowFormulaSyntaxError
from baserow.formula.parser.parser import get_parse_tree_for_formula


@extend_schema_field(OpenApiTypes.STR)
class FormulaSerializerField(serializers.CharField):
    """
    This field can be used to store a formula in the database.
    """

    def to_internal_value(self, data):
        data = super().to_internal_value(data)

        if not data:
            return data

        try:
            get_parse_tree_for_formula(data)
            return data
        except BaserowFormulaSyntaxError as e:
            raise ValidationError(f"The formula is invalid: {e}", code="invalid")
