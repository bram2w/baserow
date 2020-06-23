from decimal import Decimal
from pytz import timezone
from dateutil import parser
from dateutil.parser import ParserError
from datetime import datetime, date

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.timezone import make_aware

from rest_framework import serializers

from .registries import FieldType
from .models import (
    NUMBER_TYPE_INTEGER, NUMBER_TYPE_DECIMAL, TextField, LongTextField, NumberField,
    BooleanField, DateField
)


class TextFieldType(FieldType):
    type = 'text'
    model_class = TextField
    allowed_fields = ['text_default']
    serializer_field_names = ['text_default']

    def get_serializer_field(self, instance, **kwargs):
        return serializers.CharField(required=False, allow_null=True, allow_blank=True,
                                     default=instance.text_default, **kwargs)

    def get_model_field(self, instance, **kwargs):
        return models.TextField(default=instance.text_default, blank=True, null=True,
                                **kwargs)

    def random_value(self, instance, fake):
        return fake.name()


class LongTextFieldType(FieldType):
    type = 'long_text'
    model_class = LongTextField

    def get_serializer_field(self, instance, **kwargs):
        return serializers.CharField(required=False, allow_null=True, allow_blank=True,
                                     **kwargs)

    def get_model_field(self, instance, **kwargs):
        return models.TextField(blank=True, null=True, **kwargs)

    def random_value(self, instance, fake):
        return fake.text()


class NumberFieldType(FieldType):
    MAX_DIGITS = 50

    type = 'number'
    model_class = NumberField
    allowed_fields = ['number_type', 'number_decimal_places', 'number_negative']
    serializer_field_names = ['number_type', 'number_decimal_places', 'number_negative']

    def prepare_value_for_db(self, instance, value):
        if value and instance.number_type == NUMBER_TYPE_DECIMAL:
            value = Decimal(value)
        if value and not instance.number_negative and value < 0:
            raise ValidationError(f'The value for field {instance.id} cannot be '
                                  f'negative.')
        return value

    def get_serializer_field(self, instance, **kwargs):
        kwargs['required'] = False
        kwargs['allow_null'] = True
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

    def get_alter_column_type_function(self, connection, instance):
        if connection.vendor == 'postgresql':
            decimal_places = 0
            if instance.number_type == NUMBER_TYPE_DECIMAL:
                decimal_places = instance.number_decimal_places

            function = f"round(p_in::numeric, {decimal_places})"

            if not instance.number_negative:
                function = f"greatest({function}, 0)"

            return function

        return super().get_alter_column_type_function(connection, instance)

    def after_update(self, field, old_field, model, old_model, connection,
                     altered_column):
        """
        The allowing of negative values isn't stored in the database field type. If
        the type hasn't changed, but the allowing of negative values has it means that
        the column data hasn't been converted to positive values yet. We need to do
        this here. All the negatives values are set to 0.
        """

        if (
            not altered_column
            and not field.number_negative
            and old_field.number_negative
        ):
            model.objects.filter(**{
                f'field_{field.id}__lt': 0
            }).update(**{
                f'field_{field.id}': 0
            })


class BooleanFieldType(FieldType):
    type = 'boolean'
    model_class = BooleanField

    def get_serializer_field(self, instance, **kwargs):
        return serializers.BooleanField(required=False, default=False, **kwargs)

    def get_model_field(self, instance, **kwargs):
        return models.BooleanField(default=False, **kwargs)

    def random_value(self, instance, fake):
        return fake.pybool()


class DateFieldType(FieldType):
    type = 'date'
    model_class = DateField
    allowed_fields = ['date_format', 'date_include_time', 'date_time_format']
    serializer_field_names = ['date_format', 'date_include_time', 'date_time_format']

    def prepare_value_for_db(self, instance, value):
        """
        This method accepts a string, date object or datetime object. If the value is a
        string it will try to parse it using the dateutil's parser. Depending on the
        field's date_include_time, a date or datetime object will be returned. A
        datetime object will always have a UTC timezone. If the value is a datetime
        object with another timezone it will be converted to UTC.

        :param instance: The date field instance for which the value needs to be
            prepared.
        :type instance: DateField
        :param value: The value that needs to be prepared.
        :type value: str, date or datetime
        :return: The date or datetime field with the correct value.
        :rtype: date or datetime(tzinfo=UTC)
        :raises ValidationError: When the provided date string could not be converted
            to a date object.
        """

        if not value:
            return value

        utc = timezone('UTC')

        if type(value) == str:
            try:
                value = parser.parse(value)
            except ParserError:
                raise ValidationError('The provided string could not converted to a'
                                      'date.')

        if type(value) == date:
            value = make_aware(datetime(value.year, value.month, value.day), utc)

        if type(value) == datetime:
            value = value.astimezone(utc)
            return value if instance.date_include_time else value.date()

        raise ValidationError('The value should be a date/time string, date object or '
                              'datetime object.')

    def get_serializer_field(self, instance, **kwargs):
        kwargs['required'] = False
        kwargs['allow_null'] = True
        if instance.date_include_time:
            return serializers.DateTimeField(**kwargs)
        else:
            return serializers.DateField(**kwargs)

    def get_model_field(self, instance, **kwargs):
        kwargs['null'] = True
        kwargs['blank'] = True
        if instance.date_include_time:
            return models.DateTimeField(**kwargs)
        else:
            return models.DateField(**kwargs)

    def random_value(self, instance, fake):
        if instance.date_include_time:
            return make_aware(fake.date_time())
        else:
            return fake.date_object()
