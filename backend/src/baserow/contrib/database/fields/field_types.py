from django.db import models

from .registries import FieldType
from .models import (
    NUMBER_TYPE_INTEGER, NUMBER_TYPE_DECIMAL, TextField, NumberField, BooleanField
)


class TextFieldType(FieldType):
    type = 'text'
    model_class = TextField
    allowed_fields = ['text_default']
    serializer_field_names = ['text_default']

    def get_model_field(self, instance, **kwargs):
        return models.TextField(default=instance.text_default, null=True, blank=True,
                                **kwargs)


class NumberFieldType(FieldType):
    type = 'number'
    model_class = NumberField
    allowed_fields = ['number_type', 'number_decimal_places', 'number_negative']
    serializer_field_names = ['number_type', 'number_decimal_places', 'number_negative']

    def get_model_field(self, instance, **kwargs):
        # @TODO do something with the instance.number_negative value. There must
        # eventually be some sort of validation method in this class that checks if the
        # provided value is valid.
        kwargs['null'] = True
        kwargs['blank'] = True
        if instance.number_type == NUMBER_TYPE_INTEGER:
            return models.IntegerField(**kwargs)
        elif instance.number_type == NUMBER_TYPE_DECIMAL:
            return models.DecimalField(
                decimal_places=instance.number_decimal_places,
                max_digits=50 + instance.number_decimal_places,
                **kwargs
            )


class BooleanFieldType(FieldType):
    type = 'boolean'
    model_class = BooleanField

    def get_model_field(self, instance, **kwargs):
        return models.BooleanField(default=False, **kwargs)
