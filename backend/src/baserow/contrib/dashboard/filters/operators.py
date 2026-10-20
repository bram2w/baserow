from baserow.contrib.database.fields.models import TextField
from baserow.contrib.database.views.registries import view_filter_type_registry


def get_text_filter_operators():
    """Use the same compatible operators as a text condition in the Builder."""

    field = TextField()
    return {
        operator.type: operator
        for operator in view_filter_type_registry.get_all()
        if operator.field_is_compatible(field)
    }
