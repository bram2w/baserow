from baserow.contrib.database.fields.field_converters import RecreateFieldConverter
from baserow.contrib.database.fields.models import LongTextField, TextField

from .models import AIField


class AIFieldConverter(RecreateFieldConverter):
    type = "ai"

    def is_applicable(self, from_model, from_field, to_field):
        from_ai = isinstance(from_field, AIField)
        to_ai = isinstance(to_field, AIField)
        to_text_fields = isinstance(to_field, (TextField, LongTextField))
        return from_ai and not (to_text_fields or to_ai) or not from_ai and to_ai
