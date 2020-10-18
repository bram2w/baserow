from decimal import Decimal
from pytz import timezone
from random import randrange, randint
from dateutil import parser
from dateutil.parser import ParserError
from datetime import datetime, date

from django.db import models
from django.core.validators import URLValidator, EmailValidator
from django.core.exceptions import ValidationError
from django.utils.timezone import make_aware

from rest_framework import serializers

from baserow.contrib.database.api.fields.serializers import LinkRowValueSerializer
from baserow.contrib.database.api.fields.errors import (
    ERROR_LINK_ROW_TABLE_NOT_IN_SAME_DATABASE, ERROR_LINK_ROW_TABLE_NOT_PROVIDED
)

from .handler import FieldHandler
from .registries import FieldType
from .models import (
    NUMBER_TYPE_INTEGER, NUMBER_TYPE_DECIMAL, TextField, LongTextField, URLField,
    NumberField, BooleanField, DateField, LinkRowField, EmailField
)
from .exceptions import LinkRowTableNotInSameDatabase, LinkRowTableNotProvided


class TextFieldType(FieldType):
    type = 'text'
    model_class = TextField
    allowed_fields = ['text_default']
    serializer_field_names = ['text_default']

    def get_serializer_field(self, instance, **kwargs):
        return serializers.CharField(required=False, allow_null=True, allow_blank=True,
                                     default=instance.text_default or None, **kwargs)

    def get_model_field(self, instance, **kwargs):
        return models.TextField(default=instance.text_default or None, blank=True,
                                null=True, **kwargs)

    def random_value(self, instance, fake, cache):
        return fake.name()


class LongTextFieldType(FieldType):
    type = 'long_text'
    model_class = LongTextField

    def get_serializer_field(self, instance, **kwargs):
        return serializers.CharField(required=False, allow_null=True, allow_blank=True,
                                     **kwargs)

    def get_model_field(self, instance, **kwargs):
        return models.TextField(blank=True, null=True, **kwargs)

    def random_value(self, instance, fake, cache):
        return fake.text()


class URLFieldType(FieldType):
    type = 'url'
    model_class = URLField

    def prepare_value_for_db(self, instance, value):
        if value == '' or value is None:
            return ''

        validator = URLValidator()
        validator(value)
        return value

    def get_serializer_field(self, instance, **kwargs):
        return serializers.URLField(required=False, allow_null=True, allow_blank=True,
                                    **kwargs)

    def get_model_field(self, instance, **kwargs):
        return models.URLField(default='', blank=True, null=True, **kwargs)

    def random_value(self, instance, fake, cache):
        return fake.url()

    def get_alter_column_type_function(self, connection, instance):
        if connection.vendor == 'postgresql':
            return r"""(
            case
                when p_in::text ~* '(https?|ftps?)://(-\.)?([^\s/?\.#-]+\.?)+(/[^\s]*)?'
                then p_in::text
                else ''
                end
            )"""

        return super().get_alter_column_type_function(connection, instance)


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

    def random_value(self, instance, fake, cache):
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

    def after_update(self, from_field, to_field, from_model, to_model, user, connection,
                     altered_column):
        """
        The allowing of negative values isn't stored in the database field type. If
        the type hasn't changed, but the allowing of negative values has it means that
        the column data hasn't been converted to positive values yet. We need to do
        this here. All the negatives values are set to 0.
        """

        if (
            not altered_column
            and not to_field.number_negative
            and from_field.number_negative
        ):
            to_model.objects.filter(**{
                f'field_{to_field.id}__lt': 0
            }).update(**{
                f'field_{to_field.id}': 0
            })


class BooleanFieldType(FieldType):
    type = 'boolean'
    model_class = BooleanField

    def get_serializer_field(self, instance, **kwargs):
        return serializers.BooleanField(required=False, default=False, **kwargs)

    def get_model_field(self, instance, **kwargs):
        return models.BooleanField(default=False, **kwargs)

    def random_value(self, instance, fake, cache):
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

    def random_value(self, instance, fake, cache):
        if instance.date_include_time:
            return make_aware(fake.date_time())
        else:
            return fake.date_object()


class LinkRowFieldType(FieldType):
    """
    The link row field can be used to link a field to a row of another table. Because
    the user should also be able to see which rows are linked to the related table,
    another link row field in the related table is automatically created.
    """

    type = 'link_row'
    model_class = LinkRowField
    allowed_fields = ['link_row_table', 'link_row_related_field',
                      'link_row_relation_id']
    serializer_field_names = ['link_row_table', 'link_row_related_field']
    serializer_field_overrides = {
        'link_row_related_field': serializers.PrimaryKeyRelatedField(read_only=True)
    }
    api_exceptions_map = {
        LinkRowTableNotProvided: ERROR_LINK_ROW_TABLE_NOT_PROVIDED,
        LinkRowTableNotInSameDatabase: ERROR_LINK_ROW_TABLE_NOT_IN_SAME_DATABASE
    }
    can_sort_in_view = False

    def enhance_queryset(self, queryset, field, name):
        """
        Makes sure that the related rows are prefetched by Django.
        """

        return queryset.prefetch_related(name)

    def get_serializer_field(self, instance, **kwargs):
        """
        If the value is going to be updated we want to accept a list of integers
        representing the related row ids.
        """

        return serializers.ListField(child=serializers.IntegerField(min_value=0),
                                     required=False, **kwargs)

    def get_response_serializer_field(self, instance, **kwargs):
        """
        If a model has already been generated it will be added as a property to the
        instance. If that case then we can extract the primary field from the model and
        we can pass the name along to the LinkRowValueSerializer. It will be used to
        include the primary field's value in the response as a string.
        """

        primary_field_name = None

        if hasattr(instance, '_related_model'):
            related_model = instance._related_model
            primary_field = next(
                object
                for object in related_model._field_objects.values()
                if object['field'].primary
            )
            if primary_field:
                primary_field_name = primary_field['name']

        return LinkRowValueSerializer(many=True, value_field_name=primary_field_name,
                                      required=False, **kwargs)

    def get_serializer_help_text(self, instance):
        return 'This field accepts an `array` containing the ids of the related rows.' \
               'The response contains a list of objects containing the `id` and ' \
               'the primary field\'s `value` as a string for display purposes.'

    def get_model_field(self, instance, **kwargs):
        """
        A model field is not needed because the ManyToMany field is going to be added
        after the model has been generated.
        """

        return None

    def after_model_generation(self, instance, model, field_name, manytomany_models):
        # Store the current table's model into the manytomany_models object so that the
        # related ManyToMany field can use that one. Otherwise we end up in a recursive
        # loop.
        manytomany_models[instance.table.id] = model

        # Check if the related table model is already in the manytomany_models.
        related_model = manytomany_models.get(instance.link_row_table.id)

        # If we do not have a related table model already we can generate a new one.
        if not related_model:
            related_model = instance.link_row_table.get_model(
                manytomany_models=manytomany_models
            )

        instance._related_model = related_model
        related_name = f'reversed_field_{instance.id}'

        # Try to find the related field in the related model in order to figure out what
        # the related name should be. If the related if is not found that means that it
        # has not yet been created.
        for related_field in related_model._field_objects.values():
            if (
                isinstance(related_field['field'], self.model_class) and
                related_field['field'].link_row_related_field and
                related_field['field'].link_row_related_field.id == instance.id
            ):
                related_name = related_field['name']

        # Note that the through model will not be registered with the apps because of
        # the `DatabaseConfig.prevent_generated_model_for_registering` hack.

        models.ManyToManyField(
            to=related_model,
            related_name=related_name,
            null=True,
            blank=True,
            db_table=instance.through_table_name,
            db_constraint=False
        ).contribute_to_class(
            model,
            field_name
        )

        model_field = model._meta.get_field(field_name)
        model_field.do_related_class(
            model_field.remote_field.model,
            None
        )

    def prepare_values(self, values, user):
        """
        This method checks if the provided link row table is an int because then it
        needs to be converted to a table instance.
        """

        if 'link_row_table' in values and isinstance(values['link_row_table'], int):
            from baserow.contrib.database.table.handler import TableHandler

            values['link_row_table'] = TableHandler().get_table(
                user,
                values['link_row_table']
            )

        return values

    def before_create(self, table, primary, values, order, user):
        """
        It is not allowed to link with a table from another database. This method
        checks if the database ids are the same and if not a proper exception is
        raised.
        """

        if 'link_row_table' not in values or not values['link_row_table']:
            raise LinkRowTableNotProvided(
                'The link_row_table argument must be provided when creating a link_row '
                'field.'
            )

        link_row_table = values['link_row_table']

        if table.database_id != link_row_table.database_id:
            raise LinkRowTableNotInSameDatabase(
                f'The link row table {link_row_table.id} is not in the same database '
                f'as the table {table.id}.'
            )

    def before_update(self, from_field, to_field_values, user):
        """
        It is not allowed to link with a table from another database if the
        link_row_table has changed and if it is within the same database.
        """

        if (
            'link_row_table' not in to_field_values or
            not to_field_values['link_row_table']
        ):
            return

        link_row_table = to_field_values['link_row_table']
        table = from_field.table

        if from_field.table.database_id != link_row_table.database_id:
            raise LinkRowTableNotInSameDatabase(
                f'The link row table {link_row_table.id} is not in the same database '
                f'as the table {table.id}.'
            )

    def after_create(self, field, model, user, connection):
        """
        When the field is created we have to add the related field to the related
        table so a reversed lookup can be done by the user.
        """

        if field.link_row_related_field:
            return

        field.link_row_related_field = FieldHandler().create_field(
            user=user,
            table=field.link_row_table,
            type_name=self.type,
            do_schema_change=False,
            name=field.table.name,
            link_row_table=field.table,
            link_row_related_field=field,
            link_row_relation_id=field.link_row_relation_id
        )
        field.save()

    def before_schema_change(self, from_field, to_field, to_model, from_model,
                             from_model_field, to_model_field, user):
        if not isinstance(to_field, self.model_class):
            # If we are not going to convert to another manytomany field the
            # related field can be deleted.
            from_field.link_row_related_field.delete()
        elif (
            isinstance(to_field, self.model_class) and
            isinstance(from_field, self.model_class) and
            to_field.link_row_table.id != from_field.link_row_table.id
        ):
            # If the table has changed we have to change the following data in the
            # related field
            from_field.link_row_related_field.name = to_field.table.name
            from_field.link_row_related_field.table = to_field.link_row_table
            from_field.link_row_related_field.link_row_table = to_field.table
            from_field.link_row_related_field.order = self.model_class.get_last_order(
                to_field.link_row_table
            )
            from_field.link_row_related_field.save()

    def after_update(self, from_field, to_field, from_model, to_model, user, connection,
                     altered_column):
        """
        If the old field is not already a link row field we have to create the related
        field into the related table.
        """

        if (
            not isinstance(from_field, self.model_class) and
            isinstance(to_field, self.model_class)
        ):
            to_field.link_row_related_field = FieldHandler().create_field(
                user=user,
                table=to_field.link_row_table,
                type_name=self.type,
                do_schema_change=False,
                name=to_field.table.name,
                link_row_table=to_field.table,
                link_row_related_field=to_field,
                link_row_relation_id=to_field.link_row_relation_id
            )
            to_field.save()

    def after_delete(self, field, model, user, connection):
        """
        After the field has been deleted we also need to delete the related field.
        """

        field.link_row_related_field.delete()

    def random_value(self, instance, fake, cache):
        """
        Selects a between 0 and 3 random rows from the instance's link row table and
        return those ids in a list.
        """

        model_name = f'table_{instance.link_row_table.id}'
        count_name = f'table_{instance.link_row_table.id}_count'

        if model_name not in cache:
            cache[model_name] = instance.link_row_table.get_model()
            cache[count_name] = cache[model_name].objects.all().count()

        model = cache[model_name]
        count = cache[count_name]
        values = []

        if count == 0:
            return values

        for i in range(0, randrange(0, 3)):
            instance = model.objects.all()[randint(0, count - 1)]
            values.append(instance.id)

        return values


class EmailFieldType(FieldType):
    type = 'email'
    model_class = EmailField

    def prepare_value_for_db(self, instance, value):
        if value == '' or value is None:
            return ''

        validator = EmailValidator()
        validator(value)
        return value

    def get_serializer_field(self, instance, **kwargs):
        return serializers.EmailField(
            required=False,
            allow_null=True,
            allow_blank=True,
            **kwargs
        )

    def get_model_field(self, instance, **kwargs):
        return models.EmailField(default='', blank=True, null=True, **kwargs)

    def random_value(self, instance, fake, cache):
        return fake.email()

    def get_alter_column_type_function(self, connection, instance):
        if connection.vendor == 'postgresql':
            return r"""(
            case
                when p_in::text ~* '[A-Z0-9._+-]+@[A-Z0-9.-]+\.[A-Z]{2,}'
                then p_in::text
                else ''
                end
            )"""

        return super().get_alter_column_type_function(connection, instance)
