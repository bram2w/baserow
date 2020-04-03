from decimal import Decimal

from django.db import models
from django.core.exceptions import ValidationError

from rest_framework import serializers

from .registries import FieldType
from .models import (
    NUMBER_TYPE_INTEGER, NUMBER_TYPE_DECIMAL, TextField, NumberField, BooleanField
)


class TextFieldType(FieldType):
    type = 'text'
    model_class = TextField
    allowed_fields = ['text_default']
    serializer_field_names = ['text_default']

    def get_serializer_field(self, instance, **kwargs):
        return serializers.CharField(required=False, allow_blank=True, **kwargs)

    def get_model_field(self, instance, **kwargs):
        return models.TextField(default=instance.text_default, null=True, blank=True,
                                **kwargs)

    def random_value(self, instance, fake):
        return fake.name()


class NumberFieldType(FieldType):
    MAX_DIGITS = 50

    type = 'number'
    model_class = NumberField
    allowed_fields = ['number_type', 'number_decimal_places', 'number_negative']
    serializer_field_names = ['number_type', 'number_decimal_places', 'number_negative']

    def prepare_value_for_db(self, instance, value):
        if instance.number_type == NUMBER_TYPE_DECIMAL:
            value = Decimal(value)
        if not instance.number_negative and value < 0:
            raise ValidationError(f'The value for field {instance.id} cannot be '
                                  f'negative.')
        return value

    def get_serializer_field(self, instance, **kwargs):
        kwargs['required'] = False
        if not instance.number_negative:
            kwargs['min_value'] = 0
        if instance.number_type == NUMBER_TYPE_INTEGER:
            return serializers.IntegerField(**kwargs)
        elif instance.number_type == NUMBER_TYPE_DECIMAL:
            return serializers.DecimalField(
                decimal_places=instance.number_decimal_places,
                max_digits=self.MAX_DIGITS + instance.number_decimal_places,
                **kwargs
            )

    def get_model_field(self, instance, **kwargs):
        kwargs['null'] = True
        kwargs['blank'] = True
        if instance.number_type == NUMBER_TYPE_INTEGER:
            return models.IntegerField(**kwargs)
        elif instance.number_type == NUMBER_TYPE_DECIMAL:
            return models.DecimalField(
                decimal_places=instance.number_decimal_places,
                max_digits=self.MAX_DIGITS + instance.number_decimal_places,
                **kwargs
            )

    def random_value(self, instance, fake):
        if instance.number_type == NUMBER_TYPE_INTEGER:
            return fake.pyint(
                min_value=-10000 if instance.number_negative else 0,
                max_value=10000,
                step=1
            )
        elif instance.number_type == NUMBER_TYPE_DECIMAL:
            return fake.pydecimal(
                min_value=-10000 if instance.number_negative else 0,
                max_value=10000,
                positive=not instance.number_negative
            )


class BooleanFieldType(FieldType):
    type = 'boolean'
    model_class = BooleanField

    def get_serializer_field(self, instance, **kwargs):
        return serializers.BooleanField(required=False, **kwargs)

    def get_model_field(self, instance, **kwargs):
        return models.BooleanField(default=False, **kwargs)

    def random_value(self, instance, fake):
        return fake.pybool()
