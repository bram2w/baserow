from django.db.models import F, TextField
from django.db.models.fields.json import KT
from django.db.models.functions import Cast

from baserow.contrib.database.fields.field_types import FormulaFieldType
from baserow.contrib.database.fields.registries import field_type_registry

from .exceptions import DashboardFilterInvalidBinding

TEXT_FIELD_TYPES = {
    "text",
    "long_text",
    "email",
    "url",
    "phone_number",
    "single_select",
}


def get_text_field_type(field):
    field_type = field_type_registry.get_by_model(field)
    if isinstance(field_type, FormulaFieldType):
        _, field_type = field_type.get_field_instance_and_type_from_formula_field(field)
    if field_type.type not in TEXT_FIELD_TYPES:
        raise DashboardFilterInvalidBinding(
            "This field does not produce a supported scalar text value."
        )
    return field_type


def text_field_expression(field):
    """Compare stored text and select labels, preserving whitespace and case."""

    field_type = get_text_field_type(field)
    if field_type.type == "single_select":
        if field_type_registry.get_by_model(field).type == "formula":
            return KT(f"{field.db_column}__value")
        return F(f"{field.db_column}__value")
    return Cast(F(field.db_column), output_field=TextField())
