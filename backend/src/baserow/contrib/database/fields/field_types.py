from .registries import FieldType
from .models import TextField, NumberField, BooleanField


class TextFieldType(FieldType):
    type = 'text'
    model_class = TextField
    allowed_fields = ['text_default']
    serializer_field_names = ['text_default']


class NumberFieldType(FieldType):
    type = 'number'
    model_class = NumberField
    allowed_fields = ['number_type', 'number_decimal_places', 'number_negative']
    serializer_field_names = ['number_type', 'number_decimal_places', 'number_negative']


class BooleanFieldType(FieldType):
    type = 'boolean'
    model_class = BooleanField
