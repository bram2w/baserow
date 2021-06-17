from collections import defaultdict
from datetime import datetime, date
from decimal import Decimal
from random import randrange, randint

from dateutil import parser
from dateutil.parser import ParserError
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.core.validators import URLValidator, EmailValidator, RegexValidator
from django.db import models
from django.db.models import Case, When, Q, F, Func, Value, CharField
from django.db.models.expressions import RawSQL
from django.db.models.functions import Coalesce
from django.utils.timezone import make_aware
from pytz import timezone
from rest_framework import serializers

from baserow.contrib.database.api.fields.errors import (
    ERROR_LINK_ROW_TABLE_NOT_IN_SAME_DATABASE,
    ERROR_LINK_ROW_TABLE_NOT_PROVIDED,
    ERROR_INCOMPATIBLE_PRIMARY_FIELD_TYPE,
)
from baserow.contrib.database.api.fields.serializers import (
    LinkRowValueSerializer,
    FileFieldRequestSerializer,
    SelectOptionSerializer,
    FileFieldResponseSerializer,
)
from baserow.core.models import UserFile
from baserow.core.user_files.exceptions import UserFileDoesNotExist
from baserow.core.user_files.handler import UserFileHandler
from .exceptions import (
    LinkRowTableNotInSameDatabase,
    LinkRowTableNotProvided,
    IncompatiblePrimaryFieldTypeError,
)
from .field_filters import contains_filter, AnnotatedQ, filename_contains_filter
from .fields import SingleSelectForeignKey, URLTextField
from .handler import FieldHandler
from .models import (
    NUMBER_TYPE_INTEGER,
    NUMBER_TYPE_DECIMAL,
    TextField,
    LongTextField,
    URLField,
    NumberField,
    BooleanField,
    DateField,
    LinkRowField,
    EmailField,
    FileField,
    SingleSelectField,
    SelectOption,
    PhoneNumberField,
)
from .registries import FieldType, field_type_registry


class TextFieldType(FieldType):
    type = "text"
    model_class = TextField
    allowed_fields = ["text_default"]
    serializer_field_names = ["text_default"]

    def get_serializer_field(self, instance, **kwargs):
        return serializers.CharField(
            required=False,
            allow_null=True,
            allow_blank=True,
            default=instance.text_default or None,
            **kwargs,
        )

    def get_model_field(self, instance, **kwargs):
        return models.TextField(
            default=instance.text_default or None, blank=True, null=True, **kwargs
        )

    def random_value(self, instance, fake, cache):
        return fake.name()

    def contains_query(self, *args):
        return contains_filter(*args)


class LongTextFieldType(FieldType):
    type = "long_text"
    model_class = LongTextField

    def get_serializer_field(self, instance, **kwargs):
        return serializers.CharField(
            required=False, allow_null=True, allow_blank=True, **kwargs
        )

    def get_model_field(self, instance, **kwargs):
        return models.TextField(blank=True, null=True, **kwargs)

    def random_value(self, instance, fake, cache):
        return fake.text()

    def contains_query(self, *args):
        return contains_filter(*args)


class URLFieldType(FieldType):
    type = "url"
    model_class = URLField

    def prepare_value_for_db(self, instance, value):
        if value == "" or value is None:
            return ""

        validator = URLValidator()
        validator(value)
        return value

    def get_serializer_field(self, instance, **kwargs):
        return serializers.URLField(
            required=False, allow_null=True, allow_blank=True, **kwargs
        )

    def get_model_field(self, instance, **kwargs):
        return URLTextField(default="", blank=True, null=True, **kwargs)

    def random_value(self, instance, fake, cache):
        return fake.url()

    def get_alter_column_prepare_new_value(self, connection, from_field, to_field):
        if connection.vendor == "postgresql":
            return r"""p_in = (
            case
                when p_in::text ~* '(https?|ftps?)://(-\.)?([^\s/?\.#-]+\.?)+(/[^\s]*)?'
                then p_in::text
                else ''
                end
            );"""

        return super().get_alter_column_prepare_new_value(
            connection, from_field, to_field
        )

    def contains_query(self, *args):
        return contains_filter(*args)


class NumberFieldType(FieldType):
    MAX_DIGITS = 50

    type = "number"
    model_class = NumberField
    allowed_fields = ["number_type", "number_decimal_places", "number_negative"]
    serializer_field_names = ["number_type", "number_decimal_places", "number_negative"]

    def prepare_value_for_db(self, instance, value):
        if value is not None:
            value = Decimal(value)

        if value is not None and not instance.number_negative and value < 0:
            raise ValidationError(
                f"The value for field {instance.id} cannot be " f"negative."
            )
        return value

    def get_serializer_field(self, instance, **kwargs):
        kwargs["decimal_places"] = (
            0
            if instance.number_type == NUMBER_TYPE_INTEGER
            else instance.number_decimal_places
        )

        if not instance.number_negative:
            kwargs["min_value"] = 0

        return serializers.DecimalField(
            max_digits=self.MAX_DIGITS + kwargs["decimal_places"],
            required=False,
            allow_null=True,
            **kwargs,
        )

    def get_export_value(self, value, field_object):
        # If the number is an integer we want it to be a literal json number and so
        # don't convert it to a string. However if a decimal to preserve any precision
        # we keep it as a string.
        instance = field_object["field"]
        if instance.number_type == NUMBER_TYPE_INTEGER:
            return int(value)

        # DRF's Decimal Serializer knows how to quantize and format the decimal
        # correctly so lets use it instead of trying to do it ourselves.
        return self.get_serializer_field(instance).to_representation(value)

    def get_model_field(self, instance, **kwargs):
        kwargs["decimal_places"] = (
            0
            if instance.number_type == NUMBER_TYPE_INTEGER
            else instance.number_decimal_places
        )

        return models.DecimalField(
            max_digits=self.MAX_DIGITS + kwargs["decimal_places"],
            null=True,
            blank=True,
            **kwargs,
        )

    def random_value(self, instance, fake, cache):
        if instance.number_type == NUMBER_TYPE_INTEGER:
            return fake.pyint(
                min_value=-10000 if instance.number_negative else 0,
                max_value=10000,
                step=1,
            )
        elif instance.number_type == NUMBER_TYPE_DECIMAL:
            return fake.pydecimal(
                min_value=-10000 if instance.number_negative else 0,
                max_value=10000,
                positive=not instance.number_negative,
            )

    def get_alter_column_prepare_new_value(self, connection, from_field, to_field):
        if connection.vendor == "postgresql":
            decimal_places = 0
            if to_field.number_type == NUMBER_TYPE_DECIMAL:
                decimal_places = to_field.number_decimal_places

            function = f"round(p_in::numeric, {decimal_places})"

            if not to_field.number_negative:
                function = f"greatest({function}, 0)"

            return f"p_in = {function};"

        return super().get_alter_column_prepare_new_value(
            connection, from_field, to_field
        )

    def force_same_type_alter_column(self, from_field, to_field):
        return not to_field.number_negative and from_field.number_negative

    def contains_query(self, *args):
        return contains_filter(*args)

    def get_export_serialized_value(self, row, field_name, cache, files_zip, storage):
        value = getattr(row, field_name)
        return value if value is None else str(value)


class BooleanFieldType(FieldType):
    type = "boolean"
    model_class = BooleanField

    def get_serializer_field(self, instance, **kwargs):
        return serializers.BooleanField(required=False, default=False, **kwargs)

    def get_model_field(self, instance, **kwargs):
        return models.BooleanField(default=False, **kwargs)

    def random_value(self, instance, fake, cache):
        return fake.pybool()

    def get_export_serialized_value(self, row, field_name, cache, files_zip, storage):
        return "true" if getattr(row, field_name) else "false"

    def set_import_serialized_value(
        self, row, field_name, value, id_mapping, files_zip, storage
    ):
        setattr(row, field_name, value == "true")


class DateFieldType(FieldType):
    type = "date"
    model_class = DateField
    allowed_fields = ["date_format", "date_include_time", "date_time_format"]
    serializer_field_names = ["date_format", "date_include_time", "date_time_format"]

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

        utc = timezone("UTC")

        if type(value) == str:
            try:
                value = parser.parse(value)
            except ParserError:
                raise ValidationError(
                    "The provided string could not converted to a" "date."
                )

        if type(value) == date:
            value = make_aware(datetime(value.year, value.month, value.day), utc)

        if type(value) == datetime:
            value = value.astimezone(utc)
            return value if instance.date_include_time else value.date()

        raise ValidationError(
            "The value should be a date/time string, date object or " "datetime object."
        )

    def get_export_value(self, value, field_object):
        if value is None:
            return value
        python_format = field_object["field"].get_python_format()
        return value.strftime(python_format)

    def get_serializer_field(self, instance, **kwargs):
        kwargs["required"] = False
        kwargs["allow_null"] = True
        if instance.date_include_time:
            return serializers.DateTimeField(**kwargs)
        else:
            return serializers.DateField(**kwargs)

    def get_model_field(self, instance, **kwargs):
        kwargs["null"] = True
        kwargs["blank"] = True
        if instance.date_include_time:
            return models.DateTimeField(**kwargs)
        else:
            return models.DateField(**kwargs)

    def random_value(self, instance, fake, cache):
        if instance.date_include_time:
            return make_aware(fake.date_time())
        else:
            return fake.date_object()

    def get_alter_column_prepare_old_value(self, connection, from_field, to_field):
        """
        If the field type has changed then we want to convert the date or timestamp to
        a human readable text following the old date format.
        """

        to_field_type = field_type_registry.get_by_model(to_field)
        if to_field_type.type != self.type and connection.vendor == "postgresql":
            sql_format = from_field.get_psql_format()
            sql_type = from_field.get_psql_type()
            return f"""p_in = TO_CHAR(p_in::{sql_type}, '{sql_format}');"""

        return super().get_alter_column_prepare_old_value(
            connection, from_field, to_field
        )

    def contains_query(self, field_name, value, model_field, field):
        value = value.strip()
        # If an empty value has been provided we do not want to filter at all.
        if value == "":
            return Q()
        return AnnotatedQ(
            annotation={
                f"formatted_date_{field_name}": Coalesce(
                    Func(
                        F(field_name),
                        Value(field.get_psql_format()),
                        function="to_char",
                        output_field=CharField(),
                    ),
                    Value(""),
                )
            },
            q={f"formatted_date_{field_name}__icontains": value},
        )

    def get_alter_column_prepare_new_value(self, connection, from_field, to_field):
        """
        If the field type has changed into a date field then we want to parse the old
        text value following the format of the new field and convert it to a date or
        timestamp. If that fails we want to fallback on the default ::date or
        ::timestamp conversion that has already been added.
        """

        from_field_type = field_type_registry.get_by_model(from_field)
        if from_field_type.type != self.type and connection.vendor == "postgresql":
            sql_function = to_field.get_psql_type_convert_function()
            sql_format = to_field.get_psql_format()
            sql_type = to_field.get_psql_type()

            return f"""
                begin
                    IF char_length(p_in::text) < 5 THEN
                        p_in = null;
                    ELSEIF p_in IS NULL THEN
                        p_in = null;
                    ELSE
                        p_in = GREATEST(
                            {sql_function}(p_in::text, 'FM{sql_format}'),
                            '0001-01-01'::{sql_type}
                        );
                    END IF;
                exception when others then
                    begin
                        p_in = GREATEST(p_in::{sql_type}, '0001-01-01'::{sql_type});
                    exception when others then
                        p_in = p_default;
                    end;
                end;
            """

        return super().get_alter_column_prepare_old_value(
            connection, from_field, to_field
        )

    def get_export_serialized_value(self, row, field_name, cache, files_zip, storage):
        value = getattr(row, field_name)

        if value is None:
            return value

        return value.isoformat()

    def set_import_serialized_value(
        self, row, field_name, value, id_mapping, files_zip, storage
    ):
        if not value:
            return value

        setattr(row, field_name, datetime.fromisoformat(value))


class LinkRowFieldType(FieldType):
    """
    The link row field can be used to link a field to a row of another table. Because
    the user should also be able to see which rows are linked to the related table,
    another link row field in the related table is automatically created.
    """

    type = "link_row"
    model_class = LinkRowField
    allowed_fields = [
        "link_row_table",
        "link_row_related_field",
        "link_row_relation_id",
    ]
    serializer_field_names = ["link_row_table", "link_row_related_field"]
    serializer_field_overrides = {
        "link_row_related_field": serializers.PrimaryKeyRelatedField(read_only=True)
    }
    api_exceptions_map = {
        LinkRowTableNotProvided: ERROR_LINK_ROW_TABLE_NOT_PROVIDED,
        LinkRowTableNotInSameDatabase: ERROR_LINK_ROW_TABLE_NOT_IN_SAME_DATABASE,
        IncompatiblePrimaryFieldTypeError: ERROR_INCOMPATIBLE_PRIMARY_FIELD_TYPE,
    }
    can_order_by = False
    can_be_primary_field = False

    def enhance_queryset(self, queryset, field, name):
        """
        Makes sure that the related rows are prefetched by Django. We also want to
        enhance the primary field of the related queryset. If for example the primary
        field is a single select field then the dropdown options need to be
        prefetched in order to prevent many queries.
        """

        remote_model = queryset.model._meta.get_field(name).remote_field.model
        related_queryset = remote_model.objects.all()

        try:
            primary_field_object = next(
                object
                for object in remote_model._field_objects.values()
                if object["field"].primary
            )
            related_queryset = primary_field_object["type"].enhance_queryset(
                related_queryset,
                primary_field_object["field"],
                primary_field_object["name"],
            )
        except StopIteration:
            # If the related model does not have a primary field then we also don't
            # need to enhance the queryset.
            pass

        return queryset.prefetch_related(
            models.Prefetch(name, queryset=related_queryset)
        )

    def get_export_value(self, value, field_object):
        instance = field_object["field"]

        if hasattr(instance, "_related_model"):
            related_model = instance._related_model
            primary_field = next(
                object
                for object in related_model._field_objects.values()
                if object["field"].primary
            )
            if primary_field:
                primary_field_name = primary_field["name"]
                primary_field_type = primary_field["type"]
                primary_field_values = []
                for sub in value.all():
                    # Ensure we also convert the value from the other table to it's
                    # export form as it could be an odd field type!
                    linked_value = getattr(sub, primary_field_name)
                    if self._is_unnamed_primary_field_value(linked_value):
                        export_linked_value = f"unnamed row {sub.id}"
                    else:
                        export_linked_value = primary_field_type.get_export_value(
                            getattr(sub, primary_field_name), primary_field
                        )
                    primary_field_values.append(export_linked_value)
                return primary_field_values
        return []

    @staticmethod
    def _is_unnamed_primary_field_value(primary_field_value):
        """
        Checks if the value for a linked primary field is considered "empty".
        :param primary_field_value: The value of a primary field row in a linked table.
        :return: If this value is considered an empty primary field value.
        """

        if isinstance(primary_field_value, list):
            return len(primary_field_value) == 0
        elif isinstance(primary_field_value, dict):
            return len(primary_field_value.keys()) == 0
        else:
            return primary_field_value is None

    def get_serializer_field(self, instance, **kwargs):
        """
        If the value is going to be updated we want to accept a list of integers
        representing the related row ids.
        """

        return serializers.ListField(
            child=serializers.IntegerField(min_value=0), required=False, **kwargs
        )

    def get_response_serializer_field(self, instance, **kwargs):
        """
        If a model has already been generated it will be added as a property to the
        instance. If that is the case then we can extract the primary field from the
        model and we can pass the name along to the LinkRowValueSerializer. It will
        be used to include the primary field's value in the response as a string.
        """

        primary_field_name = None

        if hasattr(instance, "_related_model"):
            related_model = instance._related_model
            primary_field = next(
                object
                for object in related_model._field_objects.values()
                if object["field"].primary
            )
            if primary_field:
                primary_field_name = primary_field["name"]

        return serializers.ListSerializer(
            child=LinkRowValueSerializer(
                value_field_name=primary_field_name, required=False, **kwargs
            )
        )

    def get_serializer_help_text(self, instance):
        return (
            "This field accepts an `array` containing the ids of the related rows."
            "The response contains a list of objects containing the `id` and "
            "the primary field's `value` as a string for display purposes."
        )

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
        related_name = f"reversed_field_{instance.id}"

        # Try to find the related field in the related model in order to figure out what
        # the related name should be. If the related if is not found that means that it
        # has not yet been created.
        for related_field in related_model._field_objects.values():
            if (
                isinstance(related_field["field"], self.model_class)
                and related_field["field"].link_row_related_field
                and related_field["field"].link_row_related_field.id == instance.id
            ):
                related_name = related_field["name"]

        # Note that the through model will not be registered with the apps because of
        # the `DatabaseConfig.prevent_generated_model_for_registering` hack.
        models.ManyToManyField(
            to=related_model,
            related_name=related_name,
            null=True,
            blank=True,
            db_table=instance.through_table_name,
            db_constraint=False,
        ).contribute_to_class(model, field_name)

        # Trigger the newly created pending operations of all the models related to the
        # created ManyToManyField. They need to be called manually because normally
        # they are triggered when a new new model is registered. Not triggering them
        # can cause a memory leak because everytime a table model is generated, it will
        # register new pending operations.
        apps = model._meta.apps
        model_field = model._meta.get_field(field_name)
        apps.do_pending_operations(model)
        apps.do_pending_operations(related_model)
        apps.do_pending_operations(model_field.remote_field.through)
        apps.clear_cache()

    def prepare_values(self, values, user):
        """
        This method checks if the provided link row table is an int because then it
        needs to be converted to a table instance.
        """

        if "link_row_table" in values and isinstance(values["link_row_table"], int):
            from baserow.contrib.database.table.handler import TableHandler

            table = TableHandler().get_table(values["link_row_table"])
            table.database.group.has_user(user, raise_error=True)
            values["link_row_table"] = table

        return values

    def before_create(self, table, primary, values, order, user):
        """
        It is not allowed to link with a table from another database. This method
        checks if the database ids are the same and if not a proper exception is
        raised.
        """

        if "link_row_table" not in values or not values["link_row_table"]:
            raise LinkRowTableNotProvided(
                "The link_row_table argument must be provided when creating a link_row "
                "field."
            )

        link_row_table = values["link_row_table"]

        if table.database_id != link_row_table.database_id:
            raise LinkRowTableNotInSameDatabase(
                f"The link row table {link_row_table.id} is not in the same database "
                f"as the table {table.id}."
            )

    def before_update(self, from_field, to_field_values, user):
        """
        It is not allowed to link with a table from another database if the
        link_row_table has changed and if it is within the same database.
        """

        if (
            "link_row_table" not in to_field_values
            or not to_field_values["link_row_table"]
        ):
            return

        link_row_table = to_field_values["link_row_table"]
        table = from_field.table

        if from_field.table.database_id != link_row_table.database_id:
            raise LinkRowTableNotInSameDatabase(
                f"The link row table {link_row_table.id} is not in the same database "
                f"as the table {table.id}."
            )

    def after_create(self, field, model, user, connection, before):
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
            link_row_relation_id=field.link_row_relation_id,
        )
        field.save()

    def before_schema_change(
        self,
        from_field,
        to_field,
        to_model,
        from_model,
        from_model_field,
        to_model_field,
        user,
    ):
        if not isinstance(to_field, self.model_class):
            # If we are not going to convert to another manytomany field the
            # related field can be deleted.
            from_field.link_row_related_field.delete()
        elif (
            isinstance(to_field, self.model_class)
            and isinstance(from_field, self.model_class)
            and to_field.link_row_table.id != from_field.link_row_table.id
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

    def after_update(
        self,
        from_field,
        to_field,
        from_model,
        to_model,
        user,
        connection,
        altered_column,
        before,
    ):
        """
        If the old field is not already a link row field we have to create the related
        field into the related table.
        """

        if not isinstance(from_field, self.model_class) and isinstance(
            to_field, self.model_class
        ):
            to_field.link_row_related_field = FieldHandler().create_field(
                user=user,
                table=to_field.link_row_table,
                type_name=self.type,
                do_schema_change=False,
                name=to_field.table.name,
                link_row_table=to_field.table,
                link_row_related_field=to_field,
                link_row_relation_id=to_field.link_row_relation_id,
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

        model_name = f"table_{instance.link_row_table.id}"
        count_name = f"table_{instance.link_row_table.id}_count"

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

    def export_serialized(self, field):
        serialized = super().export_serialized(field, False)
        serialized["link_row_table_id"] = field.link_row_table_id
        serialized["link_row_related_field_id"] = field.link_row_related_field_id
        return serialized

    def import_serialized(self, table, serialized_values, id_mapping):
        serialized_copy = serialized_values.copy()
        serialized_copy["link_row_table_id"] = id_mapping["database_tables"][
            serialized_copy["link_row_table_id"]
        ]
        link_row_related_field_id = serialized_copy.pop("link_row_related_field_id")
        related_field_found = (
            "database_fields" in id_mapping
            and link_row_related_field_id in id_mapping["database_fields"]
        )

        if related_field_found:
            # If the related field is found, it means that it has already been
            # imported. In that case, we can directly set the `link_row_relation_id`
            # when creating the current field.
            serialized_copy["link_row_related_field_id"] = id_mapping[
                "database_fields"
            ][link_row_related_field_id]
            related_field = LinkRowField.objects.get(
                pk=serialized_copy["link_row_related_field_id"]
            )
            serialized_copy["link_row_relation_id"] = related_field.link_row_relation_id

        field = super().import_serialized(table, serialized_copy, id_mapping)

        if related_field_found:
            # If the related field is found, it means that when creating that field
            # the `link_row_relation_id` was not yet set because this field,
            # where the relation is being made to, did not yet exist. So we need to
            # set it right now.
            related_field.link_row_related_field_id = field.id
            related_field.save()
            # By returning None, the field is ignored when creating the table schema
            # and inserting the data, which is exactly what we want because the
            # through table has already been created and will result in an error if
            # we do it again.
            return None

        return field

    def get_export_serialized_value(self, row, field_name, cache, files_zip, storage):
        cache_entry = f"{field_name}_relations"
        if cache_entry not in cache:
            # In order to prevent a lot of lookup queries in the through table,
            # we want to fetch all the relations and add it to a temporary in memory
            # cache containing a mapping of the old ids to the new ids. Every relation
            # can use the cached mapped relations to find the correct id.
            cache[cache_entry] = defaultdict(list)
            through_model = row._meta.get_field(field_name).remote_field.through
            through_model_fields = through_model._meta.get_fields()
            current_field_name = through_model_fields[1].name
            relation_field_name = through_model_fields[2].name
            for relation in through_model.objects.all():
                cache[cache_entry][
                    getattr(relation, f"{current_field_name}_id")
                ].append(getattr(relation, f"{relation_field_name}_id"))

        return cache[cache_entry][row.id]

    def set_import_serialized_value(
        self, row, field_name, value, id_mapping, files_zip, storage
    ):
        getattr(row, field_name).set(value)


class EmailFieldType(FieldType):
    type = "email"
    model_class = EmailField

    def prepare_value_for_db(self, instance, value):
        if value == "" or value is None:
            return ""

        validator = EmailValidator()
        validator(value)
        return value

    def get_serializer_field(self, instance, **kwargs):
        return serializers.EmailField(
            required=False, allow_null=True, allow_blank=True, **kwargs
        )

    def get_model_field(self, instance, **kwargs):
        return models.EmailField(default="", blank=True, null=True, **kwargs)

    def random_value(self, instance, fake, cache):
        return fake.email()

    def get_alter_column_prepare_new_value(self, connection, from_field, to_field):
        if connection.vendor == "postgresql":
            return r"""p_in = (
            case
                when p_in::text ~* '[A-Z0-9._+-]+@[A-Z0-9.-]+\.[A-Z]{2,}'
                then p_in::text
                else ''
                end
            );"""

        return super().get_alter_column_prepare_new_value(
            connection, from_field, to_field
        )

    def contains_query(self, *args):
        return contains_filter(*args)


class FileFieldType(FieldType):
    type = "file"
    model_class = FileField

    def prepare_value_for_db(self, instance, value):
        if value is None:
            return []

        if not isinstance(value, list):
            raise ValidationError("The provided value must be a list.")

        if len(value) == 0:
            return []

        # Validates the provided object and extract the names from it. We need the name
        # to validate if the file actually exists and to get the 'real' properties
        # from it.
        provided_files = []
        for o in value:
            if not isinstance(o, object) or not isinstance(o.get("name"), str):
                raise ValidationError(
                    "Every provided value must at least contain "
                    "the file name as `name`."
                )

            if "visible_name" in o and not isinstance(o["visible_name"], str):
                raise ValidationError("The provided `visible_name` must be a string.")

            provided_files.append(o)

        # Create a list of the serialized UserFiles in the originally provided order
        # because that is also the order we need to store the serialized versions in.
        user_files = []
        queryset = UserFile.objects.all().name(*[f["name"] for f in provided_files])
        for file in provided_files:
            try:
                user_file = next(
                    user_file
                    for user_file in queryset
                    if user_file.name == file["name"]
                )
                serialized = user_file.serialize()
                serialized["visible_name"] = (
                    file.get("visible_name") or user_file.original_name
                )
            except StopIteration:
                raise UserFileDoesNotExist(
                    file["name"], f"The provided file {file['name']} does not exist."
                )

            user_files.append(serialized)

        return user_files

    def get_serializer_field(self, instance, **kwargs):
        return serializers.ListSerializer(
            child=FileFieldRequestSerializer(),
            required=False,
            allow_null=True,
            **kwargs,
        )

    def get_export_value(self, value, field_object):
        files = []
        for file in value:
            if "name" in file:
                path = UserFileHandler().user_file_path(file["name"])
                url = default_storage.url(path)
            else:
                url = None
            files.append(
                {
                    "visible_name": file["visible_name"],
                    "url": url,
                }
            )

        return files

    def get_response_serializer_field(self, instance, **kwargs):
        return FileFieldResponseSerializer(many=True, required=False, **kwargs)

    def get_serializer_help_text(self, instance):
        return (
            "This field accepts an `array` containing objects with the name of "
            "the file. The response contains an `array` of more detailed objects "
            "related to the files."
        )

    def get_model_field(self, instance, **kwargs):
        return JSONField(default=[], **kwargs)

    def random_value(self, instance, fake, cache):
        """
        Selects between 0 and 3 random user files and returns those serialized in a
        list.
        """

        count_name = f"field_{instance.id}_count"

        if count_name not in cache:
            cache[count_name] = UserFile.objects.all().count()

        values = []
        count = cache[count_name]

        if count == 0:
            return values

        for i in range(0, randrange(0, 3)):
            instance = UserFile.objects.all()[randint(0, count - 1)]
            serialized = instance.serialize()
            serialized["visible_name"] = serialized["name"]
            values.append(serialized)

        return values

    def contains_query(self, *args):
        return filename_contains_filter(*args)

    def get_export_serialized_value(self, row, field_name, cache, files_zip, storage):
        file_names = []
        user_file_handler = UserFileHandler()

        for file in getattr(row, field_name):
            # Check if the user file object is already in the cache and if not,
            # it must be fetched and added to to it.
            cache_entry = f"user_file_{file['name']}"
            if cache_entry not in cache:
                try:
                    user_file = UserFile.objects.all().name(file["name"]).get()
                except UserFile.DoesNotExist:
                    continue

                if file["name"] not in files_zip.namelist():
                    # Load the user file from the content and write it to the zip file
                    # because it might not exist in the environment that it is going
                    # to be imported in.
                    file_path = user_file_handler.user_file_path(user_file.name)
                    with storage.open(file_path, mode="rb") as storage_file:
                        files_zip.writestr(file["name"], storage_file.read())

                cache[cache_entry] = user_file

            file_names.append(
                {
                    "name": file["name"],
                    "visible_name": file["visible_name"],
                    "original_name": cache[cache_entry].original_name,
                }
            )
        return file_names

    def set_import_serialized_value(
        self, row, field_name, value, id_mapping, files_zip, storage
    ):
        user_file_handler = UserFileHandler()
        files = []

        for file in value:
            with files_zip.open(file["name"]) as stream:
                # Try to upload the user file with the original name to make sure
                # that if the was already uploaded, it will not be uploaded again.
                user_file = user_file_handler.upload_user_file(
                    None, file["original_name"], stream, storage=storage
                )

            value = user_file.serialize()
            value["visible_name"] = file["visible_name"]
            files.append(value)

        setattr(row, field_name, files)


class SingleSelectFieldType(FieldType):
    type = "single_select"
    model_class = SingleSelectField
    can_have_select_options = True
    allowed_fields = ["select_options"]
    serializer_field_names = ["select_options"]
    serializer_field_overrides = {
        "select_options": SelectOptionSerializer(many=True, required=False)
    }

    def enhance_queryset(self, queryset, field, name):
        return queryset.prefetch_related(
            models.Prefetch(name, queryset=SelectOption.objects.using("default").all())
        )

    def prepare_value_for_db(self, instance, value):
        if value is None:
            return value

        if isinstance(value, int):
            try:
                return SelectOption.objects.get(field=instance, id=value)
            except SelectOption.DoesNotExist:
                pass

        if isinstance(value, SelectOption) and value.field_id == instance.id:
            return value

        # If the select option is not found or if it does not belong to the right field
        # then the provided value is invalid and a validation error can be raised.
        raise ValidationError(f"The provided value is not a valid option.")

    def get_serializer_field(self, instance, **kwargs):
        return serializers.PrimaryKeyRelatedField(
            queryset=SelectOption.objects.filter(field=instance),
            required=False,
            allow_null=True,
            **kwargs,
        )

    def get_response_serializer_field(self, instance, **kwargs):
        return SelectOptionSerializer(required=False, allow_null=True, **kwargs)

    def get_serializer_help_text(self, instance):
        return (
            "This field accepts an `integer` representing the chosen select option id "
            "related to the field. Available ids can be found when getting or listing "
            "the field. The response represents chosen field, but also the value and "
            "color is exposed."
        )

    def get_export_value(self, value, field_object):
        return value.value

    def get_model_field(self, instance, **kwargs):
        return SingleSelectForeignKey(
            to=SelectOption,
            on_delete=models.SET_NULL,
            related_name="+",
            related_query_name="+",
            db_constraint=False,
            null=True,
            blank=True,
            **kwargs,
        )

    def before_create(self, table, primary, values, order, user):
        if "select_options" in values:
            return values.pop("select_options")

    def after_create(self, field, model, user, connection, before):
        if before and len(before) > 0:
            FieldHandler().update_field_select_options(user, field, before)

    def before_update(self, from_field, to_field_values, user):
        if "select_options" in to_field_values:
            FieldHandler().update_field_select_options(
                user, from_field, to_field_values["select_options"]
            )
            to_field_values.pop("select_options")

    def get_alter_column_prepare_old_value(self, connection, from_field, to_field):
        """
        If the new field type isn't a single select field we can convert the plain
        text value of the option and maybe that can be used by the new field.
        """

        to_field_type = field_type_registry.get_by_model(to_field)
        if to_field_type.type != self.type and connection.vendor == "postgresql":
            variables = {}
            values_mapping = []
            for option in from_field.select_options.all():
                variable_name = f"option_{option.id}_value"
                variables[variable_name] = option.value
                values_mapping.append(f"('{int(option.id)}', %({variable_name})s)")

            # If there are no values we don't need to convert the value to a string
            # since all values will be converted to null.
            if len(values_mapping) == 0:
                return None

            sql = f"""
                p_in = (SELECT value FROM (
                    VALUES {','.join(values_mapping)}
                ) AS values (key, value)
                WHERE key = p_in);
            """
            return sql, variables

        return super().get_alter_column_prepare_old_value(
            connection, from_field, to_field
        )

    def get_alter_column_prepare_new_value(self, connection, from_field, to_field):
        """
        If the old field wasn't a single select field we can try to match the old text
        values to the new options.
        """

        from_field_type = field_type_registry.get_by_model(from_field)
        if from_field_type.type != self.type and connection.vendor == "postgresql":
            variables = {}
            values_mapping = []
            for option in to_field.select_options.all():
                variable_name = f"option_{option.id}_value"
                variables[variable_name] = option.value
                values_mapping.append(
                    f"(lower(%({variable_name})s), '{int(option.id)}')"
                )

            # If there are no values we don't need to convert the value since all
            # values should be converted to null.
            if len(values_mapping) == 0:
                return None

            return (
                f"""p_in = (
                SELECT value FROM (
                    VALUES {','.join(values_mapping)}
                ) AS values (key, value)
                WHERE key = lower(p_in)
            );
            """,
                variables,
            )

        return super().get_alter_column_prepare_old_value(
            connection, from_field, to_field
        )

    def get_order(self, field, field_name, view_sort):
        """
        If the user wants to sort the results he expects them to be ordered
        alphabetically based on the select option value and not in the id which is
        stored in the table. This method generates a Case expression which maps the id
        to the correct position.
        """

        select_options = field.select_options.all().order_by("value")
        options = [select_option.pk for select_option in select_options]
        options.insert(0, None)

        if view_sort.order == "DESC":
            options.reverse()

        order = Case(
            *[
                When(**{field_name: option, "then": index})
                for index, option in enumerate(options)
            ]
        )
        return order

    def random_value(self, instance, fake, cache):
        """
        Selects a random choice out of the possible options.
        """

        cache_entry_name = f"field_{instance.id}_options"

        if cache_entry_name not in cache:
            cache[cache_entry_name] = instance.select_options.all()

        select_options = cache[cache_entry_name]

        # if the select_options are empty return None
        if not select_options:
            return None

        random_choice = randint(0, len(select_options) - 1)

        return select_options[random_choice]

    def contains_query(self, field_name, value, model_field, field):
        value = value.strip()
        # If an empty value has been provided we do not want to filter at all.
        if value == "":
            return Q()

        option_value_mappings = []
        option_values = []
        # We have to query for all option values here as the user table we are
        # constructing a search query for could be in a different database from the
        # SingleOption. In such a situation if we just tried to do a cross database
        # join django would crash, so we must look up the values in a separate query.

        for option in field.select_options.all():
            option_values.append(option.value)
            option_value_mappings.append(f"(lower(%s), {int(option.id)})")

        # If there are no values then there is no way this search could match this
        # field.
        if len(option_value_mappings) == 0:
            return Q()

        convert_rows_select_id_to_value_sql = f"""(
                SELECT key FROM (
                    VALUES {','.join(option_value_mappings)}
                ) AS values (key, value)
                WHERE value = "field_{field.id}"
            )
        """

        query = RawSQL(
            convert_rows_select_id_to_value_sql,
            params=option_values,
            output_field=models.CharField(),
        )
        return AnnotatedQ(
            annotation={
                f"select_option_value_{field_name}": Coalesce(query, Value(""))
            },
            q={f"select_option_value_{field_name}__icontains": value},
        )

    def get_export_serialized_value(self, row, field_name, cache, files_zip, storage):
        return getattr(row, field_name + "_id")

    def set_import_serialized_value(
        self, row, field_name, value, id_mapping, files_zip, storage
    ):
        if not value:
            return

        setattr(
            row, field_name + "_id", id_mapping["database_field_select_options"][value]
        )


class PhoneNumberFieldType(FieldType):
    """
    A simple wrapper around a TextField which ensures any entered data is a
    simple phone number.

    See `docs/decisions/001-phone-number-field-validation.md` for context
    as to why the phone number validation was implemented using a simple regex.
    """

    type = "phone_number"
    model_class = PhoneNumberField

    MAX_PHONE_NUMBER_LENGTH = 100
    """
    According to the E.164 (https://en.wikipedia.org/wiki/E.164) standard for
    international numbers the max length of an E.164 number without formatting is 15
    characters. However we allow users to store formatting characters, spaces and
    expect them to be entering numbers not in the E.164 standard but instead a
    wide range of local standards which might support longer numbers.
    This is why we have picked a very generous 100 character length to support heavily
    formatted local numbers.
    """

    PHONE_NUMBER_REGEX = rf"^[0-9NnXx,+._*()#=;/ -]{{1,{MAX_PHONE_NUMBER_LENGTH}}}$"
    """
    Allow common punctuation used in phone numbers and spaces to allow formatting,
    but otherwise don't allow text as the phone number should work as a link on mobile
    devices.
    Duplicated in the frontend code at, please keep in sync:
    web-frontend/modules/core/utils/string.js#isSimplePhoneNumber
    """

    simple_phone_number_validator = RegexValidator(regex=PHONE_NUMBER_REGEX)

    def prepare_value_for_db(self, instance, value):
        if value == "" or value is None:
            return ""
        self.simple_phone_number_validator(value)

        return value

    def get_serializer_field(self, instance, **kwargs):
        return serializers.CharField(
            required=False,
            allow_null=True,
            allow_blank=True,
            validators=[self.simple_phone_number_validator],
            max_length=self.MAX_PHONE_NUMBER_LENGTH,
            **kwargs,
        )

    def get_model_field(self, instance, **kwargs):
        return models.CharField(
            default="",
            blank=True,
            null=True,
            max_length=self.MAX_PHONE_NUMBER_LENGTH,
            validators=[self.simple_phone_number_validator],
            **kwargs,
        )

    def random_value(self, instance, fake, cache):
        return fake.phone_number()

    def get_alter_column_prepare_new_value(self, connection, from_field, to_field):
        if connection.vendor == "postgresql":
            return f"""p_in = (
            case
                when p_in::text ~* '{self.PHONE_NUMBER_REGEX}'
                then p_in::text
                else ''
                end
            );"""

        return super().get_alter_column_prepare_new_value(
            connection, from_field, to_field
        )

    def contains_query(self, *args):
        return contains_filter(*args)
