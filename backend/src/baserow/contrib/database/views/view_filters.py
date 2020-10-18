from math import floor, ceil
from pytz import timezone
from decimal import Decimal

from dateutil import parser
from dateutil.parser import ParserError

from django.db.models import Q, IntegerField, BooleanField
from django.db.models.fields.related import ManyToManyField

from baserow.contrib.database.fields.field_types import (
    TextFieldType, LongTextFieldType, URLFieldType, NumberFieldType, DateFieldType,
    LinkRowFieldType, BooleanFieldType, EmailFieldType
)

from .registries import ViewFilterType


class NotViewFilterTypeMixin:
    def get_filter(self, *args, **kwargs):
        return ~super().get_filter(*args, **kwargs)


class EqualViewFilterType(ViewFilterType):
    """
    The equal filter compared the field value to the filter value. It must be the same.
    It is compatible with models.CharField, models.TextField, models.BooleanField ('1'
    is True), models.IntegerField and models.DecimalField. It will probably also be
    compatible with other fields, but these have been tested.
    """

    type = 'equal'
    compatible_field_types = [
        TextFieldType.type,
        LongTextFieldType.type,
        URLFieldType.type,
        NumberFieldType.type,
        BooleanFieldType.type,
        EmailFieldType.type
    ]

    def get_filter(self, field_name, value, model_field):
        value = value.strip()

        # If an empty value has been provided we do not want to filter at all.
        if value == '':
            return Q()

        # Check if the model_field accepts the value.
        try:
            model_field.get_prep_value(value)
            return Q(**{field_name: value})
        except Exception:
            pass

        return Q()


class NotEqualViewFilterType(NotViewFilterTypeMixin, EqualViewFilterType):
    type = 'not_equal'


class ContainsViewFilterType(ViewFilterType):
    """
    The contains filter checks if the field value contains the provided filter value.
    It is compatible with models.CharField and models.TextField.
    """

    type = 'contains'
    compatible_field_types = [
        TextFieldType.type,
        LongTextFieldType.type,
        URLFieldType.type,
        EmailFieldType.type
    ]

    def get_filter(self, field_name, value, model_field):
        value = value.strip()

        # If an empty value has been provided we do not want to filter at all.
        if value == '':
            return Q()

        # Check if the model_field accepts the value.
        try:
            model_field.get_prep_value(value)
            return Q(**{f'{field_name}__icontains': value})
        except Exception:
            pass

        return Q()


class ContainsNotViewFilterType(NotViewFilterTypeMixin, ContainsViewFilterType):
    type = 'contains_not'


class HigherThanViewFilterType(ViewFilterType):
    """
    The higher than filter checks if the field value is higher than the filter value.
    It only works if a numeric number is provided. It is at compatible with
    models.IntegerField and models.DecimalField.
    """

    type = 'higher_than'
    compatible_field_types = [NumberFieldType.type]

    def get_filter(self, field_name, value, model_field):
        value = value.strip()

        # If an empty value has been provided we do not want to filter at all.
        if value == '':
            return Q()

        if isinstance(model_field, IntegerField) and value.find('.') != -1:
            decimal = Decimal(value)
            value = floor(decimal)

        # Check if the model_field accepts the value.
        try:
            model_field.get_prep_value(value)
            return Q(**{f'{field_name}__gt': value})
        except Exception:
            pass

        return Q()


class LowerThanViewFilterType(ViewFilterType):
    """
    The lower than filter checks if the field value is lower than the filter value.
    It only works if a numeric number is provided. It is at compatible with
    models.IntegerField and models.DecimalField.
    """

    type = 'lower_than'
    compatible_field_types = [NumberFieldType.type]

    def get_filter(self, field_name, value, model_field):
        value = value.strip()

        # If an empty value has been provided we do not want to filter at all.
        if value == '':
            return Q()

        if isinstance(model_field, IntegerField) and value.find('.') != -1:
            decimal = Decimal(value)
            value = ceil(decimal)

        # Check if the model_field accepts the value.
        try:
            model_field.get_prep_value(value)
            return Q(**{f'{field_name}__lt': value})
        except Exception:
            pass

        return Q()


class DateEqualViewFilterType(ViewFilterType):
    """
    The date filter parses the provided value as date and checks if the field value is
    the same date. It only works if a valid ISO date is provided as value and it is
    only compatible with models.DateField and models.DateTimeField.
    """

    type = 'date_equal'
    compatible_field_types = [DateFieldType.type]

    def get_filter(self, field_name, value, model_field):
        """
        Parses the provided value string and converts it to an aware datetime object.
        That object will used to make a comparison with the provided field name.
        """

        value = value.strip()

        if value == '':
            return Q()

        utc = timezone('UTC')

        try:
            datetime = parser.isoparse(value).astimezone(utc)
        except (ParserError, ValueError):
            return Q()

        # If the length if string value is lower than 10 characters we know it is only
        # a date so we can match only on year, month and day level. This way if a date
        # is provided, but if it tries to compare with a models.DateTimeField it will
        # still give back accurate results.
        if len(value) <= 10:
            return Q(**{
                f'{field_name}__year': datetime.year,
                f'{field_name}__month': datetime.month,
                f'{field_name}__day': datetime.day
            })
        else:
            return Q(**{field_name: datetime})


class DateNotEqualViewFilterType(NotViewFilterTypeMixin, DateEqualViewFilterType):
    type = 'date_not_equal'


class BooleanViewFilterType(ViewFilterType):
    """
    The boolean filter tries to convert the provided filter value to a boolean and
    compares that to the field value. If for example '1' is provided then only field
    value with True are going to be matched. This filter is compatible with
    models.BooleanField.
    """

    type = 'boolean'
    compatible_field_types = [BooleanFieldType.type]

    def get_filter(self, field_name, value, model_field):
        value = value.strip().lower()
        value = value in [
            'y',
            't',
            'o',
            'yes',
            'true',
            'on',
            '1',
        ]

        # Check if the model_field accepts the value.
        try:
            model_field.get_prep_value(value)
            return Q(**{field_name: value})
        except Exception:
            pass

        return Q()


class EmptyViewFilterType(ViewFilterType):
    """
    The empty filter checks if the field value is empty, this can be '', null,
    [] or anything. It is compatible with all fields
    """

    type = 'empty'
    compatible_field_types = [
        TextFieldType.type,
        LongTextFieldType.type,
        URLFieldType.type,
        NumberFieldType.type,
        BooleanFieldType.type,
        DateFieldType.type,
        LinkRowFieldType.type,
        EmailFieldType.type
    ]

    def get_filter(self, field_name, value, model_field):
        # If the model_field is a ManyToMany field we only have to check if it is None.
        if isinstance(model_field, ManyToManyField):
            return Q(**{f'{field_name}': None})

        if isinstance(model_field, BooleanField):
            return Q(**{f'{field_name}': False})

        q = Q(**{f'{field_name}__isnull': True})
        q.add(Q(**{f'{field_name}': None}), Q.OR)

        # If the model field accepts an empty string as value we are going to add
        # that to the or statement.
        try:
            model_field.get_prep_value('')
            q.add(Q(**{f'{field_name}': ''}), Q.OR)
        except Exception:
            pass

        return q


class NotEmptyViewFilterType(NotViewFilterTypeMixin, EmptyViewFilterType):
    type = 'not_empty'
