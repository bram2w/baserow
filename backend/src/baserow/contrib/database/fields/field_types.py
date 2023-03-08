import re
from abc import ABC, abstractmethod
from collections import defaultdict
from copy import deepcopy
from datetime import date, datetime, timedelta
from decimal import Decimal
from random import randint, randrange, sample
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple
from zipfile import ZipFile

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.aggregates import StringAgg
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError
from django.core.files.storage import Storage, default_storage
from django.db import OperationalError, models
from django.db.models import (
    CharField,
    Count,
    DateTimeField,
    F,
    Func,
    Q,
    QuerySet,
    Value,
)
from django.db.models.functions import Coalesce
from django.utils.timezone import make_aware

import pytz
from dateutil import parser
from dateutil.parser import ParserError
from loguru import logger
from pytz import timezone
from rest_framework import serializers

from baserow.contrib.database.api.fields.errors import (
    ERROR_DATE_FORCE_TIMEZONE_OFFSET_ERROR,
    ERROR_INCOMPATIBLE_PRIMARY_FIELD_TYPE,
    ERROR_INVALID_LOOKUP_TARGET_FIELD,
    ERROR_INVALID_LOOKUP_THROUGH_FIELD,
    ERROR_LINK_ROW_TABLE_NOT_IN_SAME_DATABASE,
    ERROR_LINK_ROW_TABLE_NOT_PROVIDED,
    ERROR_SELF_REFERENCING_LINK_ROW_CANNOT_HAVE_RELATED_FIELD,
    ERROR_TOO_DEEPLY_NESTED_FORMULA,
    ERROR_WITH_FORMULA,
)
from baserow.contrib.database.api.fields.serializers import (
    CollaboratorSerializer,
    FileFieldRequestSerializer,
    FileFieldResponseSerializer,
    IntegerOrStringField,
    LinkRowValueSerializer,
    MustBeEmptyField,
    SelectOptionSerializer,
)
from baserow.contrib.database.export_serialized import DatabaseExportSerializedStructure
from baserow.contrib.database.fields.field_cache import FieldCache
from baserow.contrib.database.formula import (
    BASEROW_FORMULA_TYPE_ALLOWED_FIELDS,
    BaserowExpression,
    BaserowFormulaBooleanType,
    BaserowFormulaCharType,
    BaserowFormulaDateType,
    BaserowFormulaException,
    BaserowFormulaInvalidType,
    BaserowFormulaNumberType,
    BaserowFormulaSingleSelectType,
    BaserowFormulaTextType,
    BaserowFormulaType,
    FormulaHandler,
)
from baserow.contrib.database.models import Table
from baserow.contrib.database.table.cache import invalidate_table_in_model_cache
from baserow.contrib.database.validators import UnicodeRegexValidator
from baserow.core.handler import CoreHandler
from baserow.core.models import GroupUser, UserFile
from baserow.core.user_files.exceptions import UserFileDoesNotExist
from baserow.core.user_files.handler import UserFileHandler
from baserow.core.utils import list_to_comma_separated_string

from .constants import UPSERT_OPTION_DICT_KEY
from .dependencies.exceptions import (
    CircularFieldDependencyError,
    SelfReferenceFieldDependencyError,
)
from .dependencies.handler import FieldDependants, FieldDependencyHandler
from .dependencies.models import FieldDependency
from .dependencies.types import FieldDependencies
from .exceptions import (
    AllProvidedCollaboratorIdsMustBeValidUsers,
    AllProvidedMultipleSelectValuesMustBeSelectOption,
    AllProvidedValuesMustBeIntegersOrStrings,
    DateForceTimezoneOffsetValueError,
    FieldDoesNotExist,
    IncompatiblePrimaryFieldTypeError,
    InvalidLookupTargetField,
    InvalidLookupThroughField,
    LinkRowTableNotInSameDatabase,
    LinkRowTableNotProvided,
    SelfReferencingLinkRowCannotHaveRelatedField,
)
from .field_filters import (
    AnnotatedQ,
    contains_filter,
    contains_word_filter,
    filename_contains_filter,
)
from .field_sortings import AnnotatedOrder
from .fields import (
    BaserowExpressionField,
    BaserowLastModifiedField,
    MultipleSelectManyToManyField,
    SingleSelectForeignKey,
)
from .handler import FieldHandler
from .models import (
    AbstractSelectOption,
    BooleanField,
    CreatedOnField,
    DateField,
    EmailField,
    Field,
    FileField,
    FormulaField,
    LastModifiedField,
    LinkRowField,
    LongTextField,
    LookupField,
    MultipleCollaboratorsField,
    MultipleSelectField,
    NumberField,
    PhoneNumberField,
    RatingField,
    SelectOption,
    SingleSelectField,
    TextField,
    URLField,
)
from .operations import CreateFieldOperationType, DeleteRelatedLinkRowFieldOperationType
from .registries import (
    FieldType,
    ReadOnlyFieldType,
    StartingRowType,
    field_type_registry,
)

if TYPE_CHECKING:
    from baserow.contrib.database.fields.dependencies.update_collector import (
        FieldUpdateCollector,
    )
    from baserow.contrib.database.table.models import GeneratedTableModel


class TextFieldMatchingRegexFieldType(FieldType, ABC):
    """
    This is an abstract FieldType you can extend to create a field which is a TextField
    but restricted to only allow values passing a regex. Please implement the
    regex and random_value properties.

    This abstract class will then handle all the various places that this regex needs to
    be used:
        - by setting the text field's validator
        - by setting the serializer field's validator
        - checking values passed to prepare_value_for_db pass the regex
        - by checking and only converting column values which match the regex when
          altering a column to being an email type.
    """

    @property
    @abstractmethod
    def regex(self):
        pass

    @property
    def validator(self):
        return UnicodeRegexValidator(regex_value=self.regex)

    def prepare_value_for_db(self, instance, value):
        if value == "" or value is None:
            return ""

        self.validator(value)
        return value

    def get_serializer_field(self, instance, **kwargs):
        required = kwargs.get("required", False)
        validators = kwargs.pop("validators", None) or []
        validators.append(self.validator)
        return serializers.CharField(
            **{
                "required": required,
                "allow_null": not required,
                "allow_blank": not required,
                "validators": validators,
                **kwargs,
            }
        )

    def get_model_field(self, instance, **kwargs):
        return models.TextField(
            default="",
            blank=True,
            null=True,
            validators=[self.validator],
            **kwargs,
        )

    def get_alter_column_prepare_new_value(self, connection, from_field, to_field):
        if connection.vendor == "postgresql":
            return f"""p_in = (
            case
                when p_in::text ~* '{self.regex}'
                then p_in::text
                else ''
                end
            );"""

        return super().get_alter_column_prepare_new_value(
            connection, from_field, to_field
        )

    def contains_query(self, *args):
        return contains_filter(*args)

    def contains_word_query(self, *args):
        return contains_word_filter(*args)

    def to_baserow_formula_type(self, field) -> BaserowFormulaType:
        return BaserowFormulaTextType(nullable=True)

    def from_baserow_formula_type(self, formula_type: BaserowFormulaCharType):
        return self.model_class()


class CharFieldMatchingRegexFieldType(TextFieldMatchingRegexFieldType):
    """
    This is an abstract FieldType you can extend to create a field which is a CharField
    with a specific max length, but restricted to only allow values passing a regex.
    Please implement the regex, max_length and random_value properties.

    This abstract class will then handle all the various places that this regex needs to
    be used:
        - by setting the char field's validator
        - by setting the serializer field's validator
        - checking values passed to prepare_value_for_db pass the regex
        - by checking and only converting column values which match the regex when
          altering a column to being an email type.
    """

    @property
    @abstractmethod
    def max_length(self):
        return None

    def get_serializer_field(self, instance, **kwargs):
        kwargs = {"max_length": self.max_length, **kwargs}
        return super().get_serializer_field(instance, **kwargs)

    def get_model_field(self, instance, **kwargs):
        return models.CharField(
            default="",
            blank=True,
            null=True,
            max_length=self.max_length,
            validators=[self.validator],
            **kwargs,
        )

    def to_baserow_formula_type(self, field) -> BaserowFormulaType:
        return BaserowFormulaCharType(nullable=True)


class TextFieldType(FieldType):
    type = "text"
    model_class = TextField
    allowed_fields = ["text_default"]
    serializer_field_names = ["text_default"]

    def get_serializer_field(self, instance, **kwargs):
        required = kwargs.get("required", False)
        return serializers.CharField(
            **{
                "required": required,
                "allow_null": not required,
                "allow_blank": not required,
                "default": instance.text_default or None,
                **kwargs,
            }
        )

    def get_model_field(self, instance, **kwargs):
        return models.TextField(
            default=instance.text_default or None, blank=True, null=True, **kwargs
        )

    def random_value(self, instance, fake, cache):
        return fake.name()

    def contains_query(self, *args):
        return contains_filter(*args)

    def contains_word_query(self, *args):
        return contains_word_filter(*args)

    def to_baserow_formula_type(self, field) -> BaserowFormulaType:
        return BaserowFormulaTextType(nullable=True)

    def from_baserow_formula_type(
        self, formula_type: BaserowFormulaTextType
    ) -> TextField:
        return TextField()


class LongTextFieldType(FieldType):
    type = "long_text"
    model_class = LongTextField

    def get_serializer_field(self, instance, **kwargs):
        required = kwargs.get("required", False)
        return serializers.CharField(
            **{
                "required": required,
                "allow_null": not required,
                "allow_blank": not required,
                **kwargs,
            }
        )

    def get_model_field(self, instance, **kwargs):
        return models.TextField(blank=True, null=True, **kwargs)

    def random_value(self, instance, fake, cache):
        return fake.text()

    def contains_query(self, *args):
        return contains_filter(*args)

    def contains_word_query(self, *args):
        return contains_word_filter(*args)

    def to_baserow_formula_type(self, field) -> BaserowFormulaType:
        return BaserowFormulaTextType(nullable=True)

    def from_baserow_formula_type(
        self, formula_type: BaserowFormulaTextType
    ) -> "LongTextField":
        return LongTextField()


class URLFieldType(TextFieldMatchingRegexFieldType):
    type = "url"
    model_class = URLField

    @property
    def regex(self):
        # A very lenient URL validator that allows all types of URLs as long as it
        # respects the maximal amount of characters before the dot at at least have
        # one character after the dot.
        return r"^[^\s]{0,255}(?:\.|//)[^\s]{1,}$"

    def random_value(self, instance, fake, cache):
        return fake.url()


class NumberFieldType(FieldType):
    MAX_DIGITS = 50

    type = "number"
    model_class = NumberField
    allowed_fields = ["number_decimal_places", "number_negative"]
    serializer_field_names = ["number_decimal_places", "number_negative", "number_type"]
    serializer_field_overrides = {
        "number_type": MustBeEmptyField(
            "The number_type option has been removed and can no longer be provided. "
            "Instead set number_decimal_places to 0 for an integer or 1-5 for a "
            "decimal."
        ),
        "_spectacular_annotation": {"exclude_fields": ["number_type"]},
    }

    def prepare_value_for_db(self, instance, value):
        if value is not None:
            value = Decimal(value)

        if value is not None and not instance.number_negative and value < 0:
            raise ValidationError(
                f"The value for field {instance.id} cannot be negative.",
                code="negative_not_allowed",
            )
        return value

    def get_serializer_field(self, instance: NumberField, **kwargs):
        required = kwargs.get("required", False)

        kwargs["decimal_places"] = instance.number_decimal_places

        if not instance.number_negative:
            kwargs["min_value"] = 0

        return serializers.DecimalField(
            **{
                "max_digits": self.MAX_DIGITS + kwargs["decimal_places"],
                "required": required,
                "allow_null": not required,
                **kwargs,
            }
        )

    def get_export_value(self, value, field_object, rich_value=False):
        if value is None:
            return value if rich_value else ""

        # If the number is an integer we want it to be a literal json number and so
        # don't convert it to a string. However if a decimal to preserve any precision
        # we keep it as a string.
        instance = field_object["field"]
        if instance.number_decimal_places == 0:
            return int(value)

        # DRF's Decimal Serializer knows how to quantize and format the decimal
        # correctly so lets use it instead of trying to do it ourselves.
        return self.get_serializer_field(instance).to_representation(value)

    def get_model_field(self, instance, **kwargs):
        kwargs["decimal_places"] = instance.number_decimal_places

        return models.DecimalField(
            max_digits=self.MAX_DIGITS + kwargs["decimal_places"],
            null=True,
            blank=True,
            **kwargs,
        )

    def random_value(self, instance: NumberField, fake, cache):
        if instance.number_decimal_places == 0:
            return fake.pyint(
                min_value=-10000 if instance.number_negative else 1,
                max_value=10000,
                step=1,
            )
        elif instance.number_decimal_places > 0:
            return fake.pydecimal(
                min_value=-10000 if instance.number_negative else 1,
                max_value=10000,
                positive=not instance.number_negative,
            )

    def get_alter_column_prepare_new_value(
        self, connection, from_field: NumberField, to_field
    ):
        if connection.vendor == "postgresql":
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
        value = self.get_internal_value_from_db(row, field_name)
        return value if value is None else str(value)

    def to_baserow_formula_type(self, field: NumberField) -> BaserowFormulaType:
        return BaserowFormulaNumberType(
            number_decimal_places=field.number_decimal_places, nullable=True
        )

    def from_baserow_formula_type(
        self, formula_type: BaserowFormulaNumberType
    ) -> NumberField:
        return NumberField(
            number_decimal_places=formula_type.number_decimal_places,
            number_negative=True,
        )

    def should_backup_field_data_for_same_type_update(
        self, old_field: NumberField, new_field_attrs: Dict[str, Any]
    ) -> bool:
        new_number_decimal_places = new_field_attrs.get(
            "number_decimal_places", old_field.number_decimal_places
        )
        new_number_negative = new_field_attrs.get(
            "number_negative", old_field.number_negative
        )
        return (old_field.number_decimal_places > new_number_decimal_places) or (
            old_field.number_negative and not new_number_negative
        )


class RatingFieldType(FieldType):
    type = "rating"
    model_class = RatingField
    allowed_fields = ["max_value", "color", "style"]
    serializer_field_names = ["max_value", "color", "style"]

    def prepare_value_for_db(self, instance, value):
        if not value:
            return 0

        # Ensure the value is an int
        value = int(value)

        if value < 0:
            raise ValidationError(
                "Ensure this value is greater than or equal to 0.", code="min_value"
            )
        if value > instance.max_value:
            raise ValidationError(
                f"Ensure this value is less than or equal to {instance.max_value}.",
                code="max_value",
            )

        return value

    def get_serializer_field(self, instance, **kwargs):
        return serializers.IntegerField(
            **{
                "required": False,
                "allow_null": False,
                "min_value": 0,
                "default": 0,
                "max_value": instance.max_value,
                **kwargs,
            }
        )

    def force_same_type_alter_column(self, from_field, to_field):
        """
        Force field alter column hook to be called when changing max_value.
        """

        return to_field.max_value != from_field.max_value

    def get_alter_column_prepare_new_value(self, connection, from_field, to_field):
        """
        Prepare value for Rating field. Clamp between 0 and field max_value.
        Also convert Null value to 0.
        """

        if connection.vendor == "postgresql":
            from_field_type = field_type_registry.get_by_model(from_field)

            if from_field_type.type in ["number", "text", "rating"]:
                # Convert and clamp values on field conversion
                return (
                    f"p_in = least(greatest(round(p_in::numeric), 0)"
                    f", {to_field.max_value});"
                )

            if from_field_type.type == "boolean":
                return """
                    IF p_in THEN
                        p_in = 1;
                    ELSE
                        p_in = 0;
                    END IF;
                """

        return super().get_alter_column_prepare_new_value(
            connection, from_field, to_field
        )

    def get_alter_column_prepare_old_value(self, connection, from_field, to_field):
        """
        Prepare value from Rating field.
        """

        if connection.vendor == "postgresql":
            to_field_type = field_type_registry.get_by_model(to_field)

            if to_field_type.type == "boolean":
                return "p_in = least(p_in::numeric, 1);"

        return super().get_alter_column_prepare_old_value(
            connection, from_field, to_field
        )

    def get_model_field(self, instance, **kwargs):
        return models.PositiveSmallIntegerField(
            blank=False,
            null=False,
            default=0,
            **kwargs,
        )

    def random_value(self, instance, fake, cache):
        return fake.random_int(0, instance.max_value)

    def contains_query(self, *args):
        return contains_filter(*args)

    def contains_word_query(self, *args):
        return contains_word_filter(*args)

    def to_baserow_formula_type(self, field) -> BaserowFormulaType:
        return BaserowFormulaNumberType(0)

    def from_baserow_formula_type(
        self, formula_type: BaserowFormulaNumberType
    ) -> "RatingField":
        return RatingField()

    def should_backup_field_data_for_same_type_update(
        self, old_field: RatingField, new_field_attrs: Dict[str, Any]
    ) -> bool:
        new_max_value = new_field_attrs.get("max_value", old_field.max_value)
        return old_field.max_value > new_max_value


class BooleanFieldType(FieldType):
    type = "boolean"
    model_class = BooleanField

    # lowercase serializers.BooleanField.TRUE_VALUES + "checked" keyword
    # WARNING: these values are prone to SQL injection
    TRUE_VALUES = ["t", "true", "on", "y", "yes", 1, "checked"]

    def get_alter_column_prepare_new_value(self, connection, from_field, to_field):
        """
        Prepare value for Boolean field.
        Convert to True if the text value is equal (case-insensitive) to
        'checked' or to one of the serializers.BooleanField.TRUE_VALUES.
        """

        true_values = ",".join(["'%s'" % v for v in self.TRUE_VALUES])
        return f"""
            IF lower(p_in::text) IN ({true_values}) THEN
                p_in = TRUE;
            ELSE
                p_in = FALSE;
            END IF;
        """

    def get_serializer_field(self, instance, **kwargs):
        return serializers.BooleanField(
            **{"required": False, "default": False, **kwargs}
        )

    def get_model_field(self, instance, **kwargs):
        return models.BooleanField(default=False, **kwargs)

    def random_value(self, instance, fake, cache):
        return fake.pybool()

    def get_export_serialized_value(self, row, field_name, cache, files_zip, storage):
        value = self.get_internal_value_from_db(row, field_name)
        return "true" if value else "false"

    def set_import_serialized_value(
        self, row, field_name, value, id_mapping, cache, files_zip, storage
    ):
        setattr(row, field_name, value == "true")

    def to_baserow_formula_type(self, field: NumberField) -> BaserowFormulaType:
        return BaserowFormulaBooleanType()

    def from_baserow_formula_type(
        self, boolean_formula_type: BaserowFormulaBooleanType
    ) -> BooleanField:
        return BooleanField()


class DateFieldType(FieldType):
    type = "date"
    model_class = DateField
    allowed_fields = [
        "date_format",
        "date_include_time",
        "date_time_format",
        "date_show_tzinfo",
        "date_force_timezone",
    ]
    serializer_field_names = [
        "date_format",
        "date_include_time",
        "date_time_format",
        "date_show_tzinfo",
        "date_force_timezone",
    ]
    request_serializer_field_names = serializer_field_names + [
        "date_force_timezone_offset",
    ]
    request_serializer_field_overrides = {
        "date_force_timezone_offset": serializers.IntegerField(
            required=False,
            allow_null=True,
            help_text=(
                "A UTC offset in minutes to add to all the field datetimes values.",
            ),
        )
    }
    serializer_extra_kwargs = {"date_force_timezone_offset": {"write_only": True}}
    api_exceptions_map = {
        DateForceTimezoneOffsetValueError: ERROR_DATE_FORCE_TIMEZONE_OFFSET_ERROR
    }

    def get_request_kwargs_to_backup(self, field, kwargs) -> Dict[str, Any]:
        date_force_timezone_offset = kwargs.get("date_force_timezone_offset", None)
        if date_force_timezone_offset:
            return {"date_force_timezone_offset": -date_force_timezone_offset}
        return {}

    def before_create(
        self, table, primary, allowed_field_values, order, user, field_kwargs
    ):
        force_timezone_offset = field_kwargs.get("date_force_timezone_offset", None)
        if force_timezone_offset is not None:
            raise DateForceTimezoneOffsetValueError(
                "date_force_timezone_offset is not allowed when creating a date field."
            )

    def before_update(self, from_field, to_field_values, user, field_kwargs):
        force_timezone_offset = field_kwargs.get("date_force_timezone_offset", None)
        if not isinstance(from_field, DateField):
            return

        if force_timezone_offset is not None and not to_field_values.get(
            "date_include_time", from_field.date_include_time
        ):
            raise DateForceTimezoneOffsetValueError(
                "date_include_time must be set to true"
            )

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
        to_field_kwargs,
    ):
        """
        If the date_force_timezone field is changed and
        date_force_timezone_offset is set to an integer value, we need to
        replace the timezone of all the values in the database by adding the
        utcOffset accordingly.
        """

        timezone_offset_to_add_to_replace_tz = to_field_kwargs.get(
            "date_force_timezone_offset", None
        )
        if timezone_offset_to_add_to_replace_tz is None:
            return

        to_model.objects.filter(**{f"{to_field.db_column}__isnull": False}).update(
            **{
                to_field.db_column: models.F(to_field.db_column)
                + timedelta(minutes=timezone_offset_to_add_to_replace_tz)
            }
        )

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
                # Try first to parse isodate
                value = parser.isoparse(value)
            except Exception:
                try:
                    if instance.date_format == "EU":
                        value = parser.parse(value, dayfirst=True)
                    elif instance.date_format == "ISO":
                        value = parser.parse(value, yearfirst=True)
                    else:
                        value = parser.parse(value)
                except ParserError as exc:
                    raise ValidationError(
                        "The provided string could not converted to a date.",
                        code="invalid",
                    ) from exc

        if type(value) == date:
            value = make_aware(datetime(value.year, value.month, value.day), utc)

        if type(value) == datetime:
            value = value.astimezone(utc)
            return value if instance.date_include_time else value.date()

        raise ValidationError(
            "The value should be a date/time string, date object or datetime object.",
            code="invalid",
        )

    def get_export_value(self, value, field_object, rich_value=False):
        if value is None:
            return value if rich_value else ""

        field = field_object["field"]
        if isinstance(value, datetime) and field.date_force_timezone is not None:
            value = value.astimezone(pytz.timezone(field.date_force_timezone))

        return value.strftime(field.get_python_format())

    def get_serializer_field(self, instance, **kwargs):
        required = kwargs.get("required", False)

        if instance.date_include_time:
            return serializers.DateTimeField(
                **{"required": required, "allow_null": not required, **kwargs}
            )
        else:
            return serializers.DateField(
                **{"required": required, "allow_null": not required, **kwargs}
            )

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

    def contains_query(self, field_name, value, model_field, field):
        value = value.strip()
        # If an empty value has been provided we do not want to filter at all.
        if value == "":
            return Q()

        # No user input goes into the RawSQL, safe to use.
        return AnnotatedQ(
            annotation={
                f"formatted_date_{field_name}": Coalesce(
                    Func(
                        Func(
                            # FIXME: what if date_force_timezone is None(user timezone)?
                            Value(field.date_force_timezone or "UTC"),
                            F(field_name),
                            function="timezone",
                            output_field=DateTimeField(),
                        ),
                        Value(field.get_psql_format()),
                        function="to_char",
                        output_field=CharField(),
                    ),
                    Value(""),
                )
            },
            q={f"formatted_date_{field_name}__icontains": value},
        )

    def get_alter_column_prepare_old_value(self, connection, from_field, to_field):
        """
        If the field type has changed then we want to convert the date or timestamp to
        a human readable text following the old date format.
        """

        to_field_type = field_type_registry.get_by_model(to_field)
        if to_field_type.type != self.type:
            sql_format = from_field.get_psql_format()
            variables = {}
            variable_name = f"{from_field.db_column}_timezone"
            # FIXME: what if date_force_timezone is None(user timezone)?
            variables[variable_name] = from_field.date_force_timezone or "UTC"
            return (
                f"""p_in = TO_CHAR(p_in::timestamptz at time zone %({variable_name})s,
                '{sql_format}');""",
                variables,
            )

        if (
            to_field.date_include_time is False
            and from_field.date_force_timezone is not None
        ):
            variables = {}
            variable_name = f"{from_field.db_column}_timezone"
            variables[variable_name] = from_field.date_force_timezone or "UTC"
            return (
                f"""p_in = (p_in::timestamptz at time zone %({variable_name})s)::date;""",
                variables,
            )

        return super().get_alter_column_prepare_old_value(
            connection, from_field, to_field
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
        value = self.get_internal_value_from_db(row, field_name)

        if value is None:
            return value

        return value.isoformat()

    def set_import_serialized_value(
        self, row, field_name, value, id_mapping, cache, files_zip, storage
    ):
        if not value:
            return value

        if isinstance(row._meta.get_field(field_name), models.DateTimeField):
            value = datetime.fromisoformat(value)
        else:
            value = date.fromisoformat(value)

        setattr(row, field_name, value)

    def to_baserow_formula_type(self, field: DateField) -> BaserowFormulaType:
        return BaserowFormulaDateType(
            field.date_format,
            field.date_include_time,
            field.date_time_format,
            date_force_timezone=field.date_force_timezone,
            date_show_tzinfo=field.date_show_tzinfo,
            nullable=True,
        )

    def from_baserow_formula_type(
        self, formula_type: BaserowFormulaDateType
    ) -> DateField:
        return DateField(
            date_format=formula_type.date_format,
            date_include_time=formula_type.date_include_time,
            date_time_format=formula_type.date_time_format,
            date_force_timezone=formula_type.date_force_timezone,
            date_show_tzinfo=formula_type.date_show_tzinfo,
        )

    def should_backup_field_data_for_same_type_update(
        self, old_field: DateField, new_field_attrs: Dict[str, Any]
    ) -> bool:
        new_date_include_time = new_field_attrs.get(
            "date_include_time", old_field.date_include_time
        )
        return old_field.date_include_time and not new_date_include_time


class CreatedOnLastModifiedBaseFieldType(ReadOnlyFieldType, DateFieldType):
    can_be_in_form_view = False
    field_data_is_derived_from_attrs = True

    source_field_name = None
    model_field_class = models.DateTimeField
    model_field_kwargs = {}
    populate_from_field = None

    def get_serializer_field(self, instance, **kwargs):
        if not instance.date_include_time:
            kwargs["format"] = "%Y-%m-%d"

        return serializers.DateTimeField(**{"required": False, **kwargs})

    def get_model_field(self, instance, **kwargs):
        kwargs["null"] = True
        kwargs["blank"] = True
        kwargs.update(self.model_field_kwargs)
        return self.model_field_class(**kwargs)

    def after_create(self, field, model, user, connection, before, field_kwargs):
        """
        Immediately after the field has been created, we need to populate the values
        with the already existing source_field_name column.
        """

        model.objects.all().update(
            **{f"{field.db_column}": models.F(self.source_field_name)}
        )

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
        to_field_kwargs,
    ):
        """
        If the field type has changed, we need to update the values from
        the source_field_name column.
        """

        if not isinstance(from_field, self.model_class):
            to_model.objects.all().update(
                **{f"{to_field.db_column}": models.F(self.source_field_name)}
            )

    def set_import_serialized_value(
        self, row, field_name, value, id_mapping, cache, files_zip, storage
    ):
        """
        The `auto_now_add` and `auto_now` properties are set to False during the
        import. This allows us the set the correct from the import.
        """

        if value is None:
            value = getattr(row, self.source_field_name)
        else:
            value = datetime.fromisoformat(value)

        setattr(row, field_name, value)

    def random_value(self, instance, fake, cache):
        return getattr(instance, self.source_field_name)

    def should_backup_field_data_for_same_type_update(
        self, old_field, new_field_attrs: Dict[str, Any]
    ) -> bool:
        return False


class LastModifiedFieldType(CreatedOnLastModifiedBaseFieldType):
    type = "last_modified"
    model_class = LastModifiedField
    source_field_name = "updated_on"
    model_field_class = BaserowLastModifiedField
    model_field_kwargs = {"auto_now": True}


class CreatedOnFieldType(CreatedOnLastModifiedBaseFieldType):
    type = "created_on"
    model_class = CreatedOnField
    source_field_name = "created_on"
    model_field_kwargs = {"auto_now_add": True}


class LinkRowFieldType(FieldType):
    """
    The link row field can be used to link a field to a row of another table. Because
    the user should also be able to see which rows are linked to the related table,
    another link row field in the related table is automatically created.
    """

    type = "link_row"
    model_class = LinkRowField
    allowed_fields = [
        "link_row_table_id",
        "link_row_related_field",
        "link_row_table",
        "link_row_relation_id",
    ]
    serializer_field_names = [
        "link_row_table_id",
        "link_row_related_field_id",
        "link_row_table",
        "link_row_related_field",
    ]
    serializer_field_overrides = {
        "link_row_table_id": serializers.IntegerField(
            required=False,
            allow_null=True,
            source="link_row_table.id",
            help_text="The id of the linked table.",
        ),
        "link_row_related_field_id": serializers.PrimaryKeyRelatedField(
            read_only=True, required=False, help_text="The id of the related field."
        ),
        "link_row_table": serializers.IntegerField(
            required=False,
            allow_null=True,
            source="link_row_table.id",
            help_text="(Deprecated) The id of the linked table.",
        ),
        "link_row_related_field": serializers.PrimaryKeyRelatedField(
            read_only=True,
            required=False,
            help_text="(Deprecated) The id of the related field.",
        ),
    }
    request_serializer_field_names = [
        "link_row_table_id",
        "link_row_table",
        "has_related_field",
    ]
    request_serializer_field_overrides = {
        "has_related_field": serializers.BooleanField(required=False),
        "link_row_table_id": serializers.IntegerField(
            required=False,
            allow_null=True,
            source="link_row_table.id",
            help_text="The id of the linked table.",
        ),
        "link_row_table": serializers.IntegerField(
            required=False,
            allow_null=True,
            source="link_row_table.id",
            help_text="(Deprecated) The id of the linked table.",
        ),
    }

    api_exceptions_map = {
        LinkRowTableNotProvided: ERROR_LINK_ROW_TABLE_NOT_PROVIDED,
        LinkRowTableNotInSameDatabase: ERROR_LINK_ROW_TABLE_NOT_IN_SAME_DATABASE,
        IncompatiblePrimaryFieldTypeError: ERROR_INCOMPATIBLE_PRIMARY_FIELD_TYPE,
        SelfReferencingLinkRowCannotHaveRelatedField: ERROR_SELF_REFERENCING_LINK_ROW_CANNOT_HAVE_RELATED_FIELD,
    }
    _can_order_by = False
    can_be_primary_field = False
    can_get_unique_values = False

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
            # Because we only need the primary value for serialization, we only have
            # to select and enhance that one. This will improve the performance of
            # large related tables significantly.
            related_queryset = related_queryset.only(primary_field_object["name"])
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

    def prepare_value_for_db(self, instance, value):
        return self.prepare_value_for_db_in_bulk(
            instance, {0: value}, continue_on_error=False
        )[0]

    def prepare_value_for_db_in_bulk(
        self, instance, values_by_row, continue_on_error=False
    ):
        # Create a map {value -> row_indexes} for ids and strings
        name_map = defaultdict(list)
        invalid_values = []
        for row_index, values in values_by_row.items():
            for row_name_or_id in values:
                if isinstance(row_name_or_id, int):
                    continue
                elif isinstance(row_name_or_id, str):
                    name_map[row_name_or_id].append(row_index)
                else:
                    invalid_values.append(values)
                    break

        if invalid_values:
            if continue_on_error:
                # Replace values by error for failing rows
                for row_index in invalid_values:
                    values_by_row[row_index] = AllProvidedValuesMustBeIntegersOrStrings(
                        values_by_row[row_index]
                    )
            else:
                raise ValidationError(
                    f"The provided link row values {invalid_values} are not "
                    "valid integer or string.",
                    code="invalid_value",
                )

        if name_map:
            # It's a row name -> try to get the corresponding row
            (
                related_model,
                primary_field,
            ) = self._get_related_model_and_primary_field(instance)

            primary_field_type = field_type_registry.get_by_model(
                primary_field["field"]
            )

            # Here we use the can_get_unique_values flag as it seems to filter out
            # the field types we don't want. For now we don't want the field type
            # That can't be filtered easily later like multiple_select, file field
            # or another link row field.
            # Maybe this property isn't a good fit or maybe the name can be improve
            # later.
            if not primary_field_type.can_get_unique_values:
                error = ValidationError(
                    f"The primary field type '{primary_field_type.type}' of the "
                    "linked table doesn't support text values.",
                    code="invalid_value",
                )
                if continue_on_error:
                    for row_ids in name_map.values():
                        for row_index in row_ids:
                            values_by_row[row_index] = error
                else:
                    raise error

            search_values = []
            for name, row_ids in name_map.items():
                try:
                    search_values.append(
                        primary_field_type.prepare_value_for_db(
                            primary_field["field"], name
                        )
                    )
                except ValidationError as e:
                    error = ValidationError(
                        f"The value '{name}' is an invalid value for the primary field "
                        "of the linked table.",
                        code="invalid_value",
                    )
                    if continue_on_error:
                        # Replace values by error for failing rows
                        for row_index in row_ids:
                            values_by_row[row_index] = error
                    else:
                        raise e

            # Get all matching rows
            rows = related_model.objects.filter(
                **{f"{primary_field['name']}__in": search_values}
            )

            # Map value with row id. Order is reversed to let the first row wins
            # Values are mapped back to their string representation to be compared
            # by the given text value
            row_map = {
                (
                    str(
                        primary_field["type"].get_export_value(
                            getattr(r, primary_field["name"]), primary_field
                        )
                    )
                ): r.id
                for r in rows[::-1]
            }

            rows_that_needs_name_replacement = {
                val for value in name_map.values() for val in value
            }

            # Replace all row names with actual row ids
            for row_index in rows_that_needs_name_replacement:
                values = values_by_row[row_index]
                if not isinstance(values, list):  # filter rows with exceptions
                    continue

                new_values = []
                for val in values:
                    if isinstance(val, int):
                        new_values.append(val)
                        continue

                    if val in row_map:
                        new_values.append(row_map[val])
                        continue

                    # If we get there, it's a name that doesn't exist in the linked
                    # table
                    error = ValidationError(
                        f"The provided text value '{val}' doesn't match any row in "
                        "the linked table.",
                        code="missing_row",
                    )
                    if continue_on_error:
                        values_by_row[row_index] = error
                        break
                    else:
                        raise error

                values_by_row[row_index] = new_values

        # Removes duplicate ids keeping ordering
        values_by_row = {
            k: list(dict.fromkeys(v)) if isinstance(v, list) else v
            for k, v in values_by_row.items()
        }
        return values_by_row

    def get_export_value(self, value, field_object, rich_value=False):
        def map_to_export_value(inner_value, inner_field_object):
            return inner_field_object["type"].get_export_value(
                inner_value, inner_field_object, rich_value=rich_value
            )

        result = self._get_and_map_pk_values(field_object, value, map_to_export_value)

        if rich_value:
            return result
        else:
            return list_to_comma_separated_string(result)

    def get_internal_value_from_db(
        self, row: "GeneratedTableModel", field_name: str
    ) -> List[int]:
        """
        Returns the list of ids for the related rows.

        :param row: The table row instance
        :param field_name: The name of the field.
        :return: A list of related rows ids.
        """

        related_rows = getattr(row, field_name)
        return [related_row.id for related_row in related_rows.all()]

    def get_human_readable_value(self, value, field_object):
        def map_to_human_readable_value(inner_value, inner_field_object):
            return inner_field_object["type"].get_human_readable_value(
                inner_value, inner_field_object
            )

        return ", ".join(
            self._get_and_map_pk_values(
                field_object, value, map_to_human_readable_value
            )
        )

    def _get_related_model_and_primary_field(self, instance):
        """
        Returns related model and primary field.
        """

        if hasattr(instance, "_related_model"):
            related_model = instance._related_model
        else:
            related_model = instance.link_row_table.get_model()

        primary_field = next(
            object
            for object in related_model._field_objects.values()
            if object["field"].primary
        )

        return related_model, primary_field

    def _get_and_map_pk_values(
        self, field_object, value, map_func: Callable[[Any, Dict[str, Any]], Any]
    ):
        """
        Helper function which given a linked row field pointing at another model,
        constructs a list of the related row's primary key values which are mapped by
        the provided map_func function.

        For example, Table A has Field 1 which links to Table B. Table B has a text
        primary key column. This function takes the value for a single row of
        Field 1, which is a number of related rows in Table B. It then gets
        the primary key column values for those related rows in Table B and applies
        map_func to each individual value. Finally it returns those mapped values as a
        list.

        :param value: The value of the link field in a specific row.
        :param field_object: The field object for the link field.
        :param map_func: A function to apply to each linked primary key value.
        :return: A list of mapped linked primary key values.
        """

        instance = field_object["field"]
        if hasattr(instance, "_related_model"):
            _, primary_field = self._get_related_model_and_primary_field(instance)

            if primary_field:
                primary_field_name = primary_field["name"]
                primary_field_values = []
                for sub in value.all():
                    # Ensure we also convert the value from the other table to it's
                    # appropriate form as it could be an odd field type!
                    linked_value = getattr(sub, primary_field_name)
                    if self._is_unnamed_primary_field_value(linked_value):
                        linked_pk_value = f"unnamed row {sub.id}"
                    else:
                        linked_pk_value = map_func(
                            getattr(sub, primary_field_name), primary_field
                        )
                    primary_field_values.append(linked_pk_value)
                return primary_field_values
        return []

    @staticmethod
    def _is_unnamed_primary_field_value(primary_field_value):
        """
        Checks if the value for a linked primary field is considered "unnamed".
        :param primary_field_value: The value of a primary field row in a linked table.
        :return: If this value is considered an unnamed primary field value.
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
            **{
                "child": IntegerOrStringField(min_value=0),
                "required": False,
                **kwargs,
            }
        )

    def get_response_serializer_field(self, instance, **kwargs):
        """
        If a model has already been generated it will be added as a property to the
        instance. If that is the case then we can extract the primary field from the
        model and we can pass the name along to the LinkRowValueSerializer. It will
        be used to include the primary field's value in the response as a string.
        """

        return serializers.ListSerializer(
            child=LinkRowValueSerializer(), **{"required": False, **kwargs}
        )

    def get_serializer_help_text(self, instance):
        return (
            "This field accepts an `array` containing the ids or the names of the "
            "related rows. In case of names, if the name is not found, this name "
            "is ignored. A name is the value of the primary key of the related row."
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
        manytomany_models[instance.table_id] = model

        # Check if the related table model is already in the manytomany_models.
        if instance.is_self_referencing:
            related_model = model
        else:
            related_model = manytomany_models.get(instance.link_row_table_id)
            # If we do not have a related table model already we can generate a new one.
            if related_model is None:
                related_model = instance.link_row_table.get_model(
                    manytomany_models=manytomany_models
                )

        instance._related_model = related_model
        related_name = f"reversed_field_{instance.id}"

        # Try to find the related field in the related model in order to figure out what
        # the related name should be. If the related if is not found that means that it
        # has not yet been created.
        def field_is_link_row_related_field(related_field):
            return (
                isinstance(related_field["field"], self.model_class)
                and related_field["field"].link_row_related_field_id
                and related_field["field"].link_row_related_field_id == instance.id
            )

        if not instance.is_self_referencing:
            for related_field in related_model._field_objects.values():
                if field_is_link_row_related_field(related_field):
                    related_name = related_field["name"]
                    break

        # Note that the through model will not be registered with the apps because
        # of the `DatabaseConfig.prevent_generated_model_for_registering` hack.
        models.ManyToManyField(
            to=related_model,
            related_name=related_name,
            null=True,
            blank=True,
            db_table=instance.through_table_name,
            db_constraint=False,
        ).contribute_to_class(model, field_name)

        model_field = model._meta.get_field(field_name)
        through_model = model_field.remote_field.through

        # this permits to django to find the reverse relation in the _relation_tree.
        # Look into django.db.models.options.py - _populate_directed_relation_graph
        # for more information.
        model._meta.apps.add_models(model, related_model)
        related_model._meta.apps.add_models(model, related_model)

        # Trigger the newly created pending operations of all the models related to the
        # created ManyToManyField. They need to be called manually because normally
        # they are triggered when a new model is registered. Not triggering them
        # can cause a memory leak because every time a table model is generated, it will
        # register new pending operations.
        apps = model._meta.apps
        apps.do_pending_operations(model)
        apps.do_pending_operations(related_model)
        apps.do_pending_operations(through_model)
        apps.clear_cache()

    def prepare_values(self, values, user):
        """
        This method checks if the provided link row table is an int because then it
        needs to be converted to a table instance.
        It also provided compatibility between the old name `link_row_table` and the new
        name `link_row_table_id`.
        """

        from baserow.contrib.database.table.handler import TableHandler
        from baserow.contrib.database.table.models import Table

        link_row_table_id = values.pop("link_row_table_id", None)

        if link_row_table_id is None:
            link_row_table = values.pop("link_row_table", None)

            if isinstance(link_row_table, Table):
                # set in a previous call to prepare_values, so we can use it.
                values["link_row_table"] = link_row_table
            elif isinstance(link_row_table, int):
                logger.warning(
                    "The 'link_row_table' parameter is deprecated for LinkRow field."
                    "Please, use 'link_row_table_id' instead."
                )
                link_row_table_id = link_row_table

        if isinstance(link_row_table_id, int):
            table = TableHandler().get_table(link_row_table_id)
            CoreHandler().check_permissions(
                user,
                CreateFieldOperationType.type,
                group=table.database.group,
                context=table,
            )
            values["link_row_table"] = table

        return values

    def export_prepared_values(self, field: LinkRowField):
        values = super().export_prepared_values(field)

        if field.link_row_table:
            values.pop("link_row_table", None)
            values["link_row_table_id"] = field.link_row_table_id

        # We don't want to serialize the related field as the update call will create
        # it again, but we need to save the field has a related field or not.
        values["has_related_field"] = bool(values.pop("link_row_related_field", None))

        return values

    def before_create(
        self, table, primary, allowed_field_values, order, user, field_kwargs
    ):
        """
        It is not allowed to link with a table from another database. This method
        checks if the database ids are the same and if not a proper exception is
        raised.
        """

        link_row_table = allowed_field_values.get("link_row_table")
        if link_row_table is None:
            raise LinkRowTableNotProvided(
                "The link_row_table argument must be provided when creating a link_row "
                "field."
            )

        if table.database_id != link_row_table.database_id:
            raise LinkRowTableNotInSameDatabase(
                f"The link row table {link_row_table.id} is not in the same database "
                f"as the table {table.id}."
            )

        CoreHandler().check_permissions(
            user,
            CreateFieldOperationType.type,
            table.database.group,
            context=link_row_table,
        )

        self_referencing_link_row = table.id == link_row_table.id
        create_related_field = field_kwargs.get("has_related_field")
        if self_referencing_link_row and create_related_field:
            raise SelfReferencingLinkRowCannotHaveRelatedField(
                f"A self referencing link row cannot have a related field."
            )
        if create_related_field is None:
            field_kwargs["has_related_field"] = not self_referencing_link_row

    def before_update(self, from_field, to_field_values, user, field_kwargs):
        """
        It is not allowed to link with a table from another database if the
        link_row_table has changed and if it is within the same database.
        """

        link_row_table = to_field_values.get("link_row_table")
        if link_row_table is None:
            field_kwargs.setdefault(
                "has_related_field", from_field.link_row_table_has_related_field
            )
            return

        table = from_field.table

        if from_field.table.database_id != link_row_table.database_id:
            raise LinkRowTableNotInSameDatabase(
                f"The link row table {link_row_table.id} is not in the same database "
                f"as the table {table.id}."
            )

        self_referencing_link_row = table.id == link_row_table.id
        to_field_has_related_field = field_kwargs.get("has_related_field")

        if self_referencing_link_row and to_field_has_related_field:
            raise SelfReferencingLinkRowCannotHaveRelatedField(
                f"A self referencing link row cannot have a related field."
            )

        if to_field_has_related_field is None:
            if isinstance(from_field, LinkRowField):
                field_kwargs["has_related_field"] = (
                    from_field.link_row_table_has_related_field
                    and not self_referencing_link_row
                )
            else:
                field_kwargs["has_related_field"] = not self_referencing_link_row

    def after_create(self, field, model, user, connection, before, field_kwargs):
        """
        When the field is created we have to add the related field to the related
        table so a reversed lookup can be done by the user.
        """

        if (
            field.link_row_table_has_related_field
            or field.is_self_referencing
            or not field_kwargs["has_related_field"]
        ):
            return

        related_field_name = self.find_next_unused_related_field_name(field)
        field.link_row_related_field = FieldHandler().create_field(
            user=user,
            table=field.link_row_table,
            type_name=self.type,
            do_schema_change=False,
            name=related_field_name,
            link_row_table=field.table,
            link_row_related_field=field,
            link_row_relation_id=field.link_row_relation_id,
        )
        field.save()

    # noinspection PyMethodMayBeStatic
    def find_next_unused_related_field_name(self, field):
        # First just try the tables name, so if say the Client table is linking to the
        # Address table, this field in the Address table will just be called 'Client'.
        # However say we then add another link from the Client to Address table with
        # a field name of "Bank Address", the new field in the Address table will be
        # called 'Client - Bank Address'.
        return FieldHandler().find_next_unused_field_name(
            field.link_row_table,
            [f"{field.table.name}", f"{field.table.name} - {field.name}"],
        )

    def before_schema_change(
        self,
        from_field,
        to_field,
        to_model,
        from_model,
        from_model_field,
        to_model_field,
        user,
        to_field_kwargs,
    ):
        to_instance = isinstance(to_field, self.model_class)
        from_instance = isinstance(from_field, self.model_class)
        from_link_row_table_has_related_field = (
            from_instance and from_field.link_row_table_has_related_field
        )
        to_link_row_table_has_related_field = (
            to_instance and to_field_kwargs["has_related_field"]
        )

        if to_instance:
            CoreHandler().check_permissions(
                user,
                CreateFieldOperationType.type,
                to_field.table.database.group,
                context=to_field.link_row_table,
            )

        if from_instance:
            CoreHandler().check_permissions(
                user,
                DeleteRelatedLinkRowFieldOperationType.type,
                from_field.table.database.group,
                context=from_field.link_row_table,
            )

        if (
            from_link_row_table_has_related_field
            and not to_link_row_table_has_related_field
        ):
            FieldHandler().delete_field(
                user=user,
                field=from_field.link_row_related_field,
                # Prevent the deletion of from_field itself as normally both link row
                # fields are deleted together.
                immediately_delete_only_the_provided_field=True,
            )
            if to_instance:
                to_field.link_row_related_field = None
        elif to_instance and from_instance:
            related_field_name = self.find_next_unused_related_field_name(to_field)

            if (
                not from_link_row_table_has_related_field
                and to_link_row_table_has_related_field
            ):
                # we need to create the missing link_row_related_field
                to_field.link_row_related_field = FieldHandler().create_field(
                    user=user,
                    table=to_field.link_row_table,
                    type_name=self.type,
                    name=related_field_name,
                    do_schema_change=False,
                    link_row_table=to_field.table,
                    link_row_related_field=to_field,
                    link_row_relation_id=to_field.link_row_relation_id,
                    has_related_field=True,
                )
                to_field.save()
            elif (
                from_link_row_table_has_related_field
                and to_link_row_table_has_related_field
                and from_field.link_row_table != to_field.link_row_table
            ):

                # We are changing the related fields table so we need to invalidate
                # its old model cache as this will not happen automatically.
                invalidate_table_in_model_cache(from_field.link_row_table_id)

                from_field.link_row_related_field.name = related_field_name
                from_field.link_row_related_field.table = to_field.link_row_table
                from_field.link_row_related_field.link_row_table = to_field.table
                from_field.link_row_related_field.order = (
                    self.model_class.get_last_order(to_field.link_row_table)
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
        to_field_kwargs,
    ):
        """
        If the old field is not already a link row field we have to create the related
        field into the related table. We also need to update the related field
        even if the link_row_table_has_related_field changes.
        """

        to_instance_require_related_field = (
            isinstance(to_field, self.model_class)
            and to_field_kwargs["has_related_field"]
        )
        from_instance = isinstance(from_field, self.model_class)

        if not from_instance and to_instance_require_related_field:
            related_field_name = self.find_next_unused_related_field_name(to_field)
            to_field.link_row_related_field = FieldHandler().create_field(
                user=user,
                table=to_field.link_row_table,
                type_name=self.type,
                do_schema_change=False,
                name=related_field_name,
                link_row_table=to_field.table,
                link_row_related_field=to_field,
                link_row_relation_id=to_field.link_row_relation_id,
            )
            to_field.save()

    def after_delete(self, field, model, connection):
        """
        After the field has been deleted we also need to delete the related field.
        """

        if field.link_row_related_field is not None:
            field.link_row_related_field.delete()

    def random_value(self, instance, fake, cache):
        """
        Selects a between 0 and 3 random rows from the instance's link row table and
        return those ids in a list.
        """

        model_name = f"table_{instance.link_row_table_id}"
        count_name = f"table_{instance.link_row_table_id}_count"

        if model_name not in cache:
            cache[model_name] = instance.link_row_table.get_model(field_ids=[])
            cache[count_name] = cache[model_name].objects.all().count()

        model = cache[model_name]
        count = cache[count_name]

        if count == 0:
            return []

        # Ignoring with nosec as this randint usage is purely for constructing
        # random data in dev environments and is not being used for security or
        # cryptographical reasons.
        values = model.objects.order_by("?")[0 : randrange(0, 3)].values_list(  # nosec
            "id", flat=True
        )
        return values

    def export_serialized(self, field):
        serialized = super().export_serialized(field, False)
        serialized["link_row_table_id"] = field.link_row_table_id
        serialized["link_row_related_field_id"] = field.link_row_related_field_id
        serialized["has_related_field"] = field.link_row_table_has_related_field
        return serialized

    def import_serialized(
        self,
        table: "Table",
        serialized_values: Dict[str, Any],
        id_mapping: Dict[str, Any],
    ) -> Optional[Field]:

        serialized_copy = serialized_values.copy()
        serialized_copy["link_row_table_id"] = id_mapping["database_tables"][
            serialized_copy["link_row_table_id"]
        ]
        link_row_related_field_id = serialized_copy.pop(
            "link_row_related_field_id", None
        )
        has_related_field = serialized_copy.pop(
            "has_related_field", link_row_related_field_id
        )
        related_field_found = (
            "database_fields" in id_mapping
            and has_related_field
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

    def after_import_serialized(self, field: LinkRowField, field_cache: "FieldCache"):
        if field.link_row_related_field:
            FieldDependencyHandler().rebuild_dependencies(
                field.link_row_related_field, field_cache
            )
        super().after_import_serialized(field, field_cache)

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
        self, row, field_name, value, id_mapping, cache, files_zip, storage
    ):
        getattr(row, field_name).set(value)

    def get_other_fields_to_trash_restore_always_together(self, field) -> List[Field]:
        fields = []
        if field.link_row_related_field is not None:
            fields.append(field.link_row_related_field)
        return fields

    def to_baserow_formula_type(self, field) -> BaserowFormulaType:
        primary_field = field.get_related_primary_field()
        if primary_field is None:
            return BaserowFormulaInvalidType("references unknown or deleted table")
        else:
            primary_field = primary_field.specific
            related_field_type = field_type_registry.get_by_model(primary_field)
            return related_field_type.to_baserow_formula_type(primary_field)

    def to_baserow_formula_expression(
        self, field
    ) -> BaserowExpression[BaserowFormulaType]:
        primary_field = field.get_related_primary_field()
        return FormulaHandler.get_lookup_field_reference_expression(
            field, primary_field, self.to_baserow_formula_type(field)
        )

    def get_field_dependencies(
        self, field_instance: LinkRowField, field_cache: "FieldCache"
    ) -> FieldDependencies:
        primary_related_field = field_instance.get_related_primary_field()
        if primary_related_field is not None:
            return [
                FieldDependency(
                    dependency=primary_related_field,
                    dependant=field_instance,
                    via=field_instance,
                )
            ]
        else:
            return []

    def should_backup_field_data_for_same_type_update(
        self, old_field: LinkRowField, new_field_attrs: Dict[str, Any]
    ) -> bool:
        new_link_row_table_id = new_field_attrs.get(
            "link_row_table_id", old_field.link_row_table_id
        )
        return old_field.link_row_table_id != new_link_row_table_id

    def get_dependants_which_will_break_when_field_type_changes(
        self, field: LinkRowField, to_field_type: "FieldType", field_cache: "FieldCache"
    ) -> "FieldDependants":
        """
        When a LinkRowField is converted to a different field type, the metadata row
        in the database_linkrowfield table is deleted. This causes a cascading delete
        of any FieldDependency rows which depend via this link row field. We use this
        hook to first query for these via dependencies prior to the type change and
        cascading delete so we can subsequently trigger updates for the affected
        dependant fields which previously went via this one.
        """

        # Find all FieldDependency rows which will get cascade deleted because our
        # LinkRowField row will be deleted. However we need to exclude the dependency
        # that we have via ourself as it makes no sense that we are a dependant of
        # ourself.
        return FieldDependencyHandler.get_via_dependants_of_link_field(field)


class EmailFieldType(CharFieldMatchingRegexFieldType):
    type = "email"
    model_class = EmailField

    @property
    def regex(self):
        """
        Returns a highly permissive regex which allows non-valid emails in order to keep
        the regex as simple as possible and also the same behind the frontend, database
        and python code.
        """

        # Use a lookahead to validate entire string length does exceed max length
        # as we are matching multiple different tokens in the following regex.
        lookahead = rf"(?=^.{{3,{self.max_length}}}$)"
        # See wikipedia for allowed punctuation etc:
        # https://en.wikipedia.org/wiki/Email_address#Local-part
        local_and_domain = r"[-\.\[\]!#$&*+/=?^_`{|}~\w]+"
        return rf"(?i){lookahead}^{local_and_domain}@{local_and_domain}$"

    @property
    def max_length(self):
        # max_length=254 to be compliant with RFCs 3696 and 5321
        return 254

    def random_value(self, instance, fake, cache):
        return fake.email()


class FileFieldType(FieldType):
    type = "file"
    model_class = FileField
    can_be_in_form_view = True
    can_get_unique_values = False

    def _extract_file_names(self, value):
        # Validates the provided object and extract the names from it. We need the name
        # to validate if the file actually exists and to get the 'real' properties
        # from it.
        provided_files = []
        for o in value:
            provided_files.append(o)
        return provided_files

    def prepare_value_for_db(self, instance, value):
        if value is None:
            return []

        if not isinstance(value, list):
            raise ValidationError(
                "The provided value must be a list.", code="not_a_list"
            )

        if len(value) == 0:
            return []

        provided_files = self._extract_file_names(value)

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
                raise UserFileDoesNotExist(file["name"])

            user_files.append(serialized)

        return user_files

    def prepare_value_for_db_in_bulk(
        self, instance, values_by_row, continue_on_error=False
    ):
        provided_names_by_row = {}
        name_map = defaultdict(list)

        # Create {name -> row_indexes} map
        for row_index, value in values_by_row.items():
            provided_names_by_row[row_index] = self._extract_file_names(value)
            names = [pn["name"] for pn in provided_names_by_row[row_index]]
            for name in names:
                name_map[name].append(row_index)

        if not name_map:
            return values_by_row

        unique_names = set(name_map.keys())

        # Query the database for existing files
        files = UserFile.objects.all().name(*unique_names)
        if len(files) != len(unique_names):
            invalid_names = sorted(
                list(unique_names - set((file.name) for file in files))
            )
            if continue_on_error:
                for invalid_name in invalid_names:
                    for row_index in name_map[invalid_name]:
                        values_by_row[row_index] = UserFileDoesNotExist(invalid_name)
            else:
                raise UserFileDoesNotExist(invalid_names)

        # Replacing file names by the actual file field dict
        user_files_by_name = {file.name: file for file in files}
        for row_index, value in values_by_row.items():
            # Ignore already raised exceptions
            if isinstance(value, Exception):
                continue
            serialized_files = []
            for file_names in provided_names_by_row[row_index]:
                user_file = user_files_by_name[file_names.get("name")]
                serialized = user_file.serialize()
                serialized["visible_name"] = (
                    file_names.get("visible_name") or user_file.original_name
                )
                serialized_files.append(serialized)
            values_by_row[row_index] = serialized_files

        return values_by_row

    def get_serializer_field(self, instance, **kwargs):
        required = kwargs.get("required", False)
        return serializers.ListSerializer(
            **{
                "child": FileFieldRequestSerializer(),
                "required": required,
                "allow_null": not required,
                **kwargs,
            }
        )

    def get_response_serializer_field(self, instance, **kwargs):
        return FileFieldResponseSerializer(
            **{"many": True, "required": False, **kwargs}
        )

    def get_export_value(self, value, field_object, rich_value=False):
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
                    "name": file["name"],
                    "url": url,
                }
            )

        if rich_value:
            return [{"visible_name": f["visible_name"], "url": f["url"]} for f in files]
        else:
            return list_to_comma_separated_string(
                [f'{file["visible_name"]} ({file["url"]})' for file in files]
            )

    def get_human_readable_value(self, value, field_object):
        file_names = []
        for file in value:
            file_names.append(
                file["visible_name"],
            )

        return ", ".join(file_names)

    def get_serializer_help_text(self, instance):
        return (
            "This field accepts an `array` containing objects with the name of "
            "the file. The response contains an `array` of more detailed objects "
            "related to the files."
        )

    def get_model_field(self, instance, **kwargs):
        return JSONField(default=list, **kwargs)

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

        # Ignoring with nosec as this randint usage is purely for constructing
        # random data in dev environments and is not being used for security or
        # cryptographical reasons.
        for i in range(0, randrange(0, 3)):  # nosec
            instance = UserFile.objects.all()[randint(0, count - 1)]  # nosec
            serialized = instance.serialize()
            serialized["visible_name"] = serialized["name"]
            values.append(serialized)

        return values

    def contains_query(self, *args):
        return filename_contains_filter(*args)

    def get_export_serialized_value(
        self,
        row: "GeneratedTableModel",
        field_name: str,
        cache: Dict[str, Any],
        files_zip: Optional[ZipFile] = None,
        storage: Optional[Storage] = None,
    ) -> List[Dict[str, Any]]:
        file_names = []
        user_file_handler = UserFileHandler()

        for file in self.get_internal_value_from_db(row, field_name):
            # Check if the user file object is already in the cache and if not,
            # it must be fetched and added to to it.
            cache_entry = f"user_file_{file['name']}"
            if cache_entry not in cache:
                try:
                    user_file = UserFile.objects.all().name(file["name"]).get()
                except UserFile.DoesNotExist:
                    continue

                if files_zip is not None and file["name"] not in files_zip.namelist():
                    # Load the user file from the content and write it to the zip file
                    # because it might not exist in the environment that it is going
                    # to be imported in.
                    file_path = user_file_handler.user_file_path(user_file.name)
                    with storage.open(file_path, mode="rb") as storage_file:
                        files_zip.writestr(file["name"], storage_file.read())

                cache[cache_entry] = user_file

            file_names.append(
                DatabaseExportSerializedStructure.file_field_value(
                    name=file["name"],
                    visible_name=file["visible_name"],
                    original_name=cache[cache_entry].original_name,
                )
            )
        return file_names

    def set_import_serialized_value(
        self,
        row: "GeneratedTableModel",
        field_name: str,
        value: Dict[str, Any],
        id_mapping: Dict[str, Any],
        cache: Dict[str, Any],
        files_zip: Optional[ZipFile],
        storage: Optional[Storage],
    ) -> None:
        user_file_handler = UserFileHandler()
        files = []

        for file in value:
            # files_zip could be None when files are in the same storage of the export
            # so no need to export/reimport files already present in the storage.
            if files_zip is None:
                user_file = user_file_handler.get_user_file_by_name(file["name"])
            else:
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


class SelectOptionBaseFieldType(FieldType):
    can_have_select_options = True
    allowed_fields = ["select_options"]
    serializer_field_names = ["select_options"]
    serializer_field_overrides = {
        "select_options": SelectOptionSerializer(many=True, required=False)
    }

    def before_create(
        self, table, primary, allowed_field_values, order, user, field_kwargs
    ):
        if "select_options" in allowed_field_values:
            return allowed_field_values.pop("select_options")

    def after_create(self, field, model, user, connection, before, field_kwargs):
        if before and len(before) > 0:
            FieldHandler().update_field_select_options(user, field, before)

    def before_update(self, from_field, to_field_values, user, kwargs):
        if "select_options" in to_field_values:
            FieldHandler().update_field_select_options(
                user, from_field, to_field_values["select_options"]
            )
            to_field_values.pop("select_options")

    def should_backup_field_data_for_same_type_update(
        self, old_field: SingleSelectField, new_field_attrs: Dict[str, Any]
    ) -> bool:
        updated_ids = set()
        for o in new_field_attrs.get("select_options", []):
            if UPSERT_OPTION_DICT_KEY in o:
                updated_ids.add(o[UPSERT_OPTION_DICT_KEY])
            if "id" in o:
                updated_ids.add(o["id"])

        # If there are any deleted options we need to backup
        return old_field.select_options.exclude(id__in=updated_ids).exists()


class SingleSelectFieldType(SelectOptionBaseFieldType):
    type = "single_select"
    model_class = SingleSelectField

    def get_serializer_field(self, instance, **kwargs):
        required = kwargs.get("required", False)
        field_serializer = IntegerOrStringField(
            **{
                "required": required,
                "allow_null": not required,
                **kwargs,
            },
        )
        return field_serializer

    def get_response_serializer_field(self, instance, **kwargs):
        required = kwargs.get("required", False)
        return SelectOptionSerializer(
            **{
                "required": required,
                "allow_null": not required,
                "many": False,
                **kwargs,
            }
        )

    def enhance_queryset(self, queryset, field, name):
        return queryset.prefetch_related(
            models.Prefetch(name, queryset=SelectOption.objects.using("default").all())
        )

    def get_value_for_filter(self, row: "GeneratedTableModel", field_name: str) -> int:
        return getattr(row, field_name).value

    def get_internal_value_from_db(
        self, row: "GeneratedTableModel", field_name: str
    ) -> int:
        return getattr(row, f"{field_name}_id")

    def prepare_value_for_db(self, instance, value):
        return self.prepare_value_for_db_in_bulk(
            instance, {0: value}, continue_on_error=False
        )[0]

    def prepare_value_for_db_in_bulk(
        self, instance, values_by_row, continue_on_error=False
    ):

        # Create a map {names/ids -> row_indexes} and extract unique int and text values
        unique_ids = set()
        unique_names = set()
        invalid_values_by_index = {}

        for row_index, value in values_by_row.items():
            if value is None:
                continue

            if isinstance(value, SelectOption):
                continue
            elif isinstance(value, int):
                unique_ids.add(value)
            elif isinstance(value, str):
                unique_names.add(value)
            else:
                error = ValidationError(
                    f"The provided value {value} is not a valid option.",
                    code="invalid_option",
                )
                if continue_on_error:
                    invalid_values_by_index[row_index] = error
                else:
                    raise error

        invalid_values_by_index.update(invalid_values_by_index)

        # Query database with all these gathered values
        select_options = SelectOption.objects.filter(field=instance).filter(
            Q(id__in=unique_ids) | Q(value__in=unique_names)
        )

        # Create a map {id|value -> option}
        # Here we reverse the select_options list to let the first option
        # win in the map in case of duplicate for text values.
        option_map = {opt.value: opt for opt in select_options[::-1]}
        option_map.update({opt.id: opt for opt in select_options})

        found_option_values = set(option_map.keys())
        unique_values = unique_ids | unique_names

        invalid_values = sorted(
            [str(val) for val in list(unique_values - found_option_values)]
        )

        # Whether invalid values exists ?
        if invalid_values:
            if not continue_on_error:
                # Fail fast
                raise AllProvidedMultipleSelectValuesMustBeSelectOption(invalid_values)

        # Replace original values by real option object if possible
        for row_index, value in values_by_row.items():
            # Ignore empty and select values
            if value is None or isinstance(value, SelectOption):
                continue
            if continue_on_error and value not in option_map:
                values_by_row[row_index] = ValidationError(
                    f"The provided value {value} is not a valid option.",
                    code="invalid_option",
                )
            else:
                values_by_row[row_index] = option_map[value]

        return values_by_row

    def get_serializer_help_text(self, instance):
        return (
            "This field accepts an `integer` representing the chosen select option id "
            "related to the field. Available ids can be found when getting or listing "
            "the field. The response represents chosen field, but also the value and "
            "color is exposed."
        )

    def get_export_value(self, value, field_object, rich_value=False):
        if value is None:
            return None if rich_value else ""
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

            # Has been checked for issues, everything is properly escaped and safe.
            # fmt: off
            sql = (  # nosec b608
                f"""
                p_in = (SELECT value FROM (
                    VALUES {','.join(values_mapping)}
                ) AS values (key, value)
                WHERE key = p_in);
                """
            )
            # fmt: on
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

            # Has been checked for issues, everything is properly escaped and safe.
            return (  # nosec
                f"""p_in = (
                SELECT value FROM (
                    VALUES {','.join(values_mapping)}
                ) AS values (key, value)
                WHERE key = lower(p_in)
            );
            """,
                variables,
            )

        return super().get_alter_column_prepare_new_value(
            connection, from_field, to_field
        )

    def get_order(self, field, field_name, order_direction) -> AnnotatedOrder:
        """
        If the user wants to sort the results he expects them to be ordered
        alphabetically based on the select option value and not in the id which is
        stored in the table. This method generates a Case expression which maps the id
        to the correct position.
        """

        order = F(f"{field_name}__value")
        if order_direction == "ASC":
            order = order.asc(nulls_first=True)
        else:
            order = order.desc(nulls_last=True)
        return AnnotatedOrder(order=order)

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

        # Ignoring with nosec as this randint usage is purely for constructing random
        # data in dev environments and is not being used for security or cryptographical
        # reasons.
        random_choice = randint(0, len(select_options) - 1)  # nosec

        return select_options[random_choice]

    def contains_query(self, field_name, value, model_field, field):
        value = value.strip()
        # If an empty value has been provided we do not want to filter at all.
        if value == "":
            return Q()
        return Q(**{f"{field_name}__value__icontains": value})

    def contains_word_query(self, field_name, value, model_field, field):
        value = value.strip()
        # If an empty value has been provided we do not want to filter at all.
        if value == "":
            return Q()
        value = re.escape(value)
        return Q(**{f"{field_name}__value__iregex": rf"\m{value}\M"})

    def set_import_serialized_value(
        self, row, field_name, value, id_mapping, cache, files_zip, storage
    ):
        select_option_mapping = id_mapping["database_field_select_options"]

        if not value or value not in select_option_mapping:
            return

        setattr(row, field_name + "_id", select_option_mapping[value])

    def to_baserow_formula_type(self, field):
        return BaserowFormulaSingleSelectType(nullable=True)

    def from_baserow_formula_type(self, formula_type) -> Field:
        return self.model_class()


class MultipleSelectFieldType(SelectOptionBaseFieldType):
    type = "multiple_select"
    model_class = MultipleSelectField
    can_get_unique_values = False

    def get_serializer_field(self, instance, **kwargs):
        required = kwargs.get("required", False)
        field_serializer = IntegerOrStringField(
            **{
                "required": required,
                "allow_null": not required,
                **kwargs,
            },
        )
        return serializers.ListSerializer(
            child=field_serializer, required=required, **kwargs
        )

    def get_value_for_filter(self, row: "GeneratedTableModel", field_name: str) -> str:
        related_objects = getattr(row, field_name)
        values = [related_object.value for related_object in related_objects.all()]
        return list_to_comma_separated_string(values)

    def get_internal_value_from_db(
        self, row: "GeneratedTableModel", field_name: str
    ) -> List[int]:
        related_objects = getattr(row, field_name)
        return [related_object.id for related_object in related_objects.all()]

    def get_response_serializer_field(self, instance, **kwargs):
        required = kwargs.get("required", False)
        return SelectOptionSerializer(
            **{
                "required": required,
                "allow_null": not required,
                "many": True,
                **kwargs,
            }
        )

    def enhance_queryset(self, queryset, field, name):
        return queryset.prefetch_related(name)

    def prepare_value_for_db(self, instance, value):
        return self.prepare_value_for_db_in_bulk(
            instance, {0: value}, continue_on_error=False
        )[0]

    def prepare_value_for_db_in_bulk(
        self, instance, values_by_row, continue_on_error=False
    ):
        # Create a map {value -> row_indexes} for ids and strings
        id_map = defaultdict(list)
        name_map = defaultdict(list)
        invalid_values = []
        for row_index, values in values_by_row.items():
            for value in values:
                if isinstance(value, int):
                    id_map[value].append(row_index)
                elif isinstance(value, str):
                    name_map[value].append(row_index)
                else:
                    if continue_on_error:
                        invalid_values.append(values)
                        break
                    else:
                        # Fail on first error
                        raise AllProvidedValuesMustBeIntegersOrStrings(values)

        if invalid_values:
            # Replace values by error for failing rows
            for row_index in invalid_values:
                values_by_row[row_index] = AllProvidedValuesMustBeIntegersOrStrings(
                    values_by_row[row_index]
                )

        if id_map:
            # Query database for existing options
            option_from_ids = SelectOption.objects.filter(
                field=instance, id__in=id_map.keys()
            ).values_list("id", flat=True)

            if len(option_from_ids) != len(id_map):
                invalid_ids = sorted(list(set(id_map.keys()) - set(option_from_ids)))
                if continue_on_error:
                    # Replace values by error for failing rows
                    for invalid_name in invalid_ids:
                        for row_index in id_map[invalid_name]:
                            values_by_row[
                                row_index
                            ] = AllProvidedMultipleSelectValuesMustBeSelectOption(
                                invalid_name
                            )
                else:
                    # or fail fast
                    raise AllProvidedMultipleSelectValuesMustBeSelectOption(invalid_ids)

        if name_map:
            # Query database for existing options
            options_from_names = list(
                SelectOption.objects.filter(field=instance, value__in=name_map.keys())
            )
            # Remove duplicate names
            found_option_names = set([opt.value for opt in options_from_names])

            if len(name_map) != len(found_option_names):
                invalid_names = sorted(list(set(name_map.keys()) - found_option_names))
                if continue_on_error:
                    # Replace values by error for failing rows
                    for invalid_name in invalid_names:
                        for row_index in name_map[invalid_name]:
                            values_by_row[
                                row_index
                            ] = AllProvidedMultipleSelectValuesMustBeSelectOption(
                                invalid_name
                            )

                else:
                    # or fail fast
                    raise AllProvidedMultipleSelectValuesMustBeSelectOption(
                        invalid_names
                    )

            # Map {name -> opt} reverse list to let the first value win in the map
            opt_map = {opt.value: opt for opt in options_from_names[::-1]}

            rows_that_needs_name_replacement = {
                val for value in name_map.values() for val in value
            }

            # Replace all option names with actual option ids
            for row_index in rows_that_needs_name_replacement:
                value = values_by_row[row_index]
                if isinstance(value, list):  # filter rows with exceptions
                    values_by_row[row_index] = [
                        opt_map[val].id if isinstance(val, str) else val
                        for val in value
                    ]

        # Removes duplicate ids while keeping ordering
        values_by_row = {
            k: list(dict.fromkeys(v)) if isinstance(v, list) else v
            for k, v in values_by_row.items()
        }
        return values_by_row

    def get_serializer_help_text(self, instance):
        return (
            "This field accepts a list of `integer` each of which representing the "
            "chosen select option id related to the field. Available ids can be found"
            "when getting or listing the field. The response represents chosen field, "
            "but also the value and color is exposed."
        )

    def random_value(self, instance, fake, cache):
        """
        Selects a random sublist out of the possible options.
        """

        cache_entry_name = f"field_{instance.id}_options"

        if cache_entry_name not in cache:
            cache[cache_entry_name] = instance.select_options.all()

        select_options = cache[cache_entry_name]

        # if the select_options are empty return empty list
        if not select_options:
            return None

        # Ignoring with nosec as this randint usage is purely for constructing random
        # data in dev environments and is not being used for security or cryptographical
        # reasons.
        random_choice = randint(1, len(select_options))  # nosec

        return sample([x.id for x in select_options], random_choice)

    def get_export_value(self, value, field_object, rich_value=False):
        if value is None:
            return value if rich_value else ""

        result = [item.value for item in value.all()]

        if rich_value:
            return result
        else:
            return list_to_comma_separated_string(result)

    def get_human_readable_value(self, value, field_object):
        export_value = self.get_export_value(value, field_object, rich_value=True)

        return ", ".join(export_value)

    def get_model_field(self, instance, **kwargs):
        return None

    def after_model_generation(self, instance, model, field_name, manytomany_models):
        select_option_meta = type(
            "Meta",
            (AbstractSelectOption.Meta,),
            {
                "managed": False,
                "app_label": model._meta.app_label,
                "db_tablespace": model._meta.db_tablespace,
                "db_table": "database_selectoption",
                "apps": model._meta.apps,
            },
        )
        select_option_model = type(
            str(f"MultipleSelectField{instance.id}SelectOption"),
            (AbstractSelectOption,),
            {
                "Meta": select_option_meta,
                "field": models.ForeignKey(
                    Field, on_delete=models.CASCADE, related_name="+"
                ),
                "__module__": model.__module__,
                "_generated_table_model": True,
            },
        )
        related_name = f"reversed_field_{instance.id}"
        shared_kwargs = {
            "null": True,
            "blank": True,
            "db_table": instance.through_table_name,
            "db_constraint": False,
        }

        MultipleSelectManyToManyField(
            to=select_option_model, related_name=related_name, **shared_kwargs
        ).contribute_to_class(model, field_name)
        MultipleSelectManyToManyField(
            to=model, related_name=field_name, **shared_kwargs
        ).contribute_to_class(select_option_model, related_name)

        # Trigger the newly created pending operations of all the models related to the
        # created ManyToManyField. They need to be called manually because normally
        # they are triggered when a new model is registered. Not triggering them
        # can cause a memory leak because everytime a table model is generated, it will
        # register new pending operations.
        apps = model._meta.apps
        model_field = model._meta.get_field(field_name)
        select_option_field = select_option_model._meta.get_field(related_name)
        apps.do_pending_operations(model)
        apps.do_pending_operations(select_option_model)
        apps.do_pending_operations(model_field.remote_field.through)
        apps.do_pending_operations(model)
        apps.do_pending_operations(select_option_field.remote_field.through)
        apps.clear_cache()

    def get_export_serialized_value(self, row, field_name, cache, files_zip, storage):
        cache_entry = f"{field_name}_relations"
        if cache_entry not in cache:
            # In order to prevent a lot of lookup queries in the through table, we want
            # to fetch all the relations and add it to a temporary in memory cache
            # containing a mapping of the old ids to the new ids. Every relation can
            # use the cached mapped relations to find the correct id.
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
        self, row, field_name, value, id_mapping, cache, files_zip, storage
    ):
        mapped_values = [
            id_mapping["database_field_select_options"][item] for item in value
        ]
        getattr(row, field_name).set(mapped_values)

    def contains_query(self, field_name, value, model_field, field):
        value = value.strip()
        # If an empty value has been provided we do not want to filter at all.
        if value == "":
            return Q()

        query = StringAgg(f"{field_name}__value", ",")

        return AnnotatedQ(
            annotation={
                f"select_option_value_{field_name}": Coalesce(query, Value(""))
            },
            q={f"select_option_value_{field_name}__icontains": value},
        )

    def contains_word_query(self, field_name, value, model_field, field):
        value = value.strip()
        # If an empty value has been provided we do not want to filter at all.
        if value == "":
            return Q()
        value = re.escape(value)
        query = StringAgg(f"{field_name}__value", " ")

        return AnnotatedQ(
            annotation={
                f"select_option_value_{field_name}": Coalesce(query, Value(""))
            },
            q={f"select_option_value_{field_name}__iregex": rf"\m{value}\M"},
        )

    def get_order(self, field, field_name, order_direction):
        """
        If the user wants to sort the results he expects them to be ordered
        alphabetically based on the select option value and not in the id which is
        stored in the table. This method generates a Case expression which maps the id
        to the correct position.
        """

        sort_column_name = f"{field_name}_agg_sort"
        query = Coalesce(StringAgg(f"{field_name}__value", ","), Value(""))
        annotation = {sort_column_name: query}

        order = F(sort_column_name)
        if order_direction == "DESC":
            order = order.desc(nulls_first=True)
        else:
            order = order.asc(nulls_first=True)

        return AnnotatedOrder(annotation=annotation, order=order)

    def before_field_options_update(
        self, field, to_create=None, to_update=None, to_delete=None
    ):
        """
        Before removing the select options, we want to delete the link between
        the row and the options.
        """

        through_model = (
            field.table.get_model(fields=[field], field_ids=[])
            ._meta.get_field(field.db_column)
            .remote_field.through
        )
        through_model_fields = through_model._meta.get_fields()
        option_field_name = through_model_fields[2].name
        through_model.objects.filter(**{f"{option_field_name}__in": to_delete}).delete()


class PhoneNumberFieldType(CharFieldMatchingRegexFieldType):
    """
    A simple wrapper around a TextField which ensures any entered data is a
    simple phone number.

    See `docs/decisions/001-phone-number-field-validation.md` for context
    as to why the phone number validation was implemented using a simple regex.
    """

    type = "phone_number"
    model_class = PhoneNumberField

    MAX_PHONE_NUMBER_LENGTH = 100

    @property
    def regex(self):
        """
        Allow common punctuation used in phone numbers and spaces to allow formatting,
        but otherwise don't allow text as the phone number should work as a link on
        mobile devices.
        Duplicated in the frontend code at, please keep in sync:
        web-frontend/modules/core/utils/string.js#isSimplePhoneNumber
        """

        return rf"^[0-9NnXx,+._*()#=;/ -]{{1,{self.max_length}}}$"

    @property
    def max_length(self):
        """
        According to the E.164 (https://en.wikipedia.org/wiki/E.164) standard for
        international numbers the max length of an E.164 number without formatting is 15
        characters. However we allow users to store formatting characters, spaces and
        expect them to be entering numbers not in the E.164 standard but instead a
        wide range of local standards which might support longer numbers.
        This is why we have picked a very generous 100 character length to support
        heavily formatted local numbers.
        """

        return self.MAX_PHONE_NUMBER_LENGTH

    def random_value(self, instance, fake, cache):
        return fake.phone_number()


class FormulaFieldType(ReadOnlyFieldType):
    type = "formula"
    model_class = FormulaField

    can_be_in_form_view = False
    field_data_is_derived_from_attrs = True
    needs_refresh_after_import_serialized = True

    CORE_FORMULA_FIELDS = [
        "formula",
        "formula_type",
    ]
    allowed_fields = BASEROW_FORMULA_TYPE_ALLOWED_FIELDS + CORE_FORMULA_FIELDS
    serializer_field_names = BASEROW_FORMULA_TYPE_ALLOWED_FIELDS + CORE_FORMULA_FIELDS
    serializer_field_overrides = {
        "error": serializers.CharField(required=False, read_only=True),
        "nullable": serializers.BooleanField(required=False, read_only=True),
    }

    @staticmethod
    def _stack_error_mapper(e):
        return (
            ERROR_TOO_DEEPLY_NESTED_FORMULA
            if "stack depth limit exceeded" in str(e)
            else None
        )

    api_exceptions_map = {
        BaserowFormulaException: ERROR_WITH_FORMULA,
        OperationalError: _stack_error_mapper,
    }

    @staticmethod
    def compatible_with_formula_types(*compatible_formula_types: List[str]):
        def checker(field) -> bool:
            from baserow.contrib.database.fields.registries import field_type_registry

            field_type = field_type_registry.get_by_model(field.specific_class)
            if isinstance(field_type, FormulaFieldType):
                formula_type = field.specific.cached_formula_type
                return formula_type.type in compatible_formula_types
            else:
                return False

        return checker

    def _get_field_instance_and_type_from_formula_field(
        self,
        formula_field_instance: FormulaField,
    ) -> Tuple[Field, FieldType]:
        """
        Gets the BaserowFormulaType the provided formula field currently has and the
        Baserow FieldType used to work with a formula of that formula type.

        :param formula_field_instance: An instance of a formula field.
        :return: The BaserowFormulaType of the formula field instance.
        """

        formula_type = self.to_baserow_formula_type(formula_field_instance)
        return formula_type.get_baserow_field_instance_and_type()

    def get_serializer_field(self, instance: FormulaField, **kwargs):
        (
            field_instance,
            field_type,
        ) = self._get_field_instance_and_type_from_formula_field(instance)
        return field_type.get_serializer_field(field_instance, **kwargs)

    def get_response_serializer_field(self, instance, **kwargs):
        (
            field_instance,
            field_type,
        ) = self._get_field_instance_and_type_from_formula_field(instance)
        return field_type.get_response_serializer_field(field_instance, **kwargs)

    def get_model_field(self, instance: FormulaField, **kwargs):
        # When typed_table is False we are constructing a table model without
        # doing any type checking, we can't know what the expression is in this
        # case but we still want to generate a model field so the model can be
        # used to do SQL operations like dropping fields etc.
        if not (instance.error or instance.trashed):
            expression = self.to_baserow_formula_expression(instance)
        else:
            expression = None

        (
            field_instance,
            field_type,
        ) = self._get_field_instance_and_type_from_formula_field(instance)
        expression_field_type = field_type.get_model_field(field_instance, **kwargs)

        # Depending on the `expression_field_type` class level state is changed when
        # the field is __init__'ed. This means to prevent different sub types polluting
        # this class level state of other runtime instances we need a unique class
        # per subtype.
        # noinspection PyPep8Naming
        SpecializedBaserowExpressionField = type(
            expression_field_type.__class__.__name__ + "BaserowExpressionField",
            (BaserowExpressionField,),
            {},
        )
        return SpecializedBaserowExpressionField(
            null=True,
            blank=True,
            expression=expression,
            expression_field=expression_field_type,
            requires_refresh_after_insert=instance.requires_refresh_after_insert,
            **kwargs,
        )

    def prepare_value_for_db(self, instance, value):
        """
        Since the Formula Field is a read only field, we raise a
        ValidationError when there is a value present.
        """

        if not value:
            return value

        raise ValidationError(
            f"Field of type {self.type} is read only and should not be set manually.",
            code="read_only",
        )

    def get_export_value(
        self, value, field_object, rich_value=False
    ) -> BaserowFormulaType:
        instance = field_object["field"]
        (
            field_instance,
            field_type,
        ) = self._get_field_instance_and_type_from_formula_field(instance)
        return field_type.get_export_value(
            value,
            {"field": field_instance, "type": field_type, "name": field_object["name"]},
            rich_value=rich_value,
        )

    def contains_query(self, field_name, value, model_field, field: FormulaField):
        (
            field_instance,
            field_type,
        ) = self._get_field_instance_and_type_from_formula_field(field)
        return field_type.contains_query(field_name, value, model_field, field_instance)

    def contains_word_query(self, field_name, value, model_field, field):
        (
            field_instance,
            field_type,
        ) = self._get_field_instance_and_type_from_formula_field(field)
        return field_type.contains_word_query(
            field_name, value, model_field, field_instance
        )

    def get_alter_column_prepare_old_value(self, connection, from_field, to_field):
        (
            field_instance,
            field_type,
        ) = self._get_field_instance_and_type_from_formula_field(from_field)
        return field_type.get_alter_column_prepare_old_value(
            connection, field_instance, to_field
        )

    def to_baserow_formula_type(self, field: FormulaField) -> BaserowFormulaType:
        return field.cached_formula_type

    def to_baserow_formula_expression(
        self, field: FormulaField
    ) -> BaserowExpression[BaserowFormulaType]:
        return FormulaHandler.get_typed_internal_expression_from_field(field)

    def get_field_dependencies(
        self, field_instance: FormulaField, field_cache: "FieldCache"
    ) -> FieldDependencies:
        return FormulaHandler.get_field_dependencies(field_instance, field_cache)

    def get_human_readable_value(self, value: Any, field_object) -> str:
        (
            field_instance,
            field_type,
        ) = self._get_field_instance_and_type_from_formula_field(field_object["field"])
        return field_type.get_human_readable_value(
            value,
            {
                "field": field_instance,
                "type": field_type,
                "name": field_object["name"],
            },
        )

    def restore_failed(self, field_instance, restore_exception):
        handleable_exceptions_to_error = {
            SelfReferenceFieldDependencyError: "After restoring references itself "
            "which is impossible",
            CircularFieldDependencyError: "After restoring would causes a circular "
            "reference between fields",
        }
        exception_type = type(restore_exception)
        if exception_type in handleable_exceptions_to_error:
            BaserowFormulaInvalidType(
                handleable_exceptions_to_error[exception_type]
            ).persist_onto_formula_field(field_instance)
            field_instance.save(recalculate=False)
            return True
        else:
            return False

    def get_fields_needing_periodic_update(self) -> Optional[QuerySet]:

        return (
            FormulaField.objects.filter(needs_periodic_update=True)
            .annotate(num_dependencies=Count("field_dependencies"))
            .filter(num_dependencies=0)
        )

    def run_periodic_update(
        self,
        field: Field,
        update_collector: "Optional[FieldUpdateCollector]" = None,
        field_cache: "Optional[FieldCache]" = None,
        via_path_to_starting_table: Optional[List[LinkRowField]] = None,
    ):
        from baserow.contrib.database.fields.dependencies.update_collector import (
            FieldUpdateCollector,
        )

        should_send_signals_at_end = False

        if update_collector is None:
            # We are the outermost call, and so we should send all the signals
            # when we finish.
            should_send_signals_at_end = True
            update_collector = FieldUpdateCollector(field.table)

        if field_cache is None:
            field_cache = FieldCache()
        if via_path_to_starting_table is None:
            via_path_to_starting_table = []

        self._refresh_row_values(
            field, update_collector, field_cache, via_path_to_starting_table
        )

        for (
            dependant_field,
            dependant_field_type,
            path_to_starting_table,
        ) in field.dependant_fields_with_types(field_cache, via_path_to_starting_table):
            dependant_field_type.run_periodic_update(
                dependant_field,
                update_collector,
                field_cache,
                path_to_starting_table,
            )

        if should_send_signals_at_end:
            update_collector.apply_updates_and_get_updated_fields(field_cache)
            update_collector.send_force_refresh_signals_for_all_updated_tables()

    def row_of_dependency_updated(
        self,
        field: FormulaField,
        starting_row: "StartingRowType",
        update_collector: "FieldUpdateCollector",
        field_cache: "FieldCache",
        via_path_to_starting_table: Optional[List[LinkRowField]],
    ):
        self._refresh_row_values_if_not_in_starting_table(
            field, update_collector, field_cache, via_path_to_starting_table
        )
        super().row_of_dependency_updated(
            field,
            starting_row,
            update_collector,
            field_cache,
            via_path_to_starting_table,
        )

    def _refresh_row_values_if_not_in_starting_table(
        self,
        field: FormulaField,
        update_collector: "FieldUpdateCollector",
        field_cache: "FieldCache",
        via_path_to_starting_table: Optional[List[LinkRowField]],
    ):
        if (
            via_path_to_starting_table is not None
            and len(via_path_to_starting_table) > 0
        ):
            self._refresh_row_values(
                field, update_collector, field_cache, via_path_to_starting_table
            )

    def _refresh_row_values(
        self,
        field: FormulaField,
        update_collector: "FieldUpdateCollector",
        field_cache: "FieldCache",
        via_path_to_starting_table: Optional[List[LinkRowField]],
    ):
        update_statement = (
            FormulaHandler.baserow_expression_to_update_django_expression(
                field.cached_typed_internal_expression,
                field_cache.get_model(field.table),
            )
        )
        update_collector.add_field_with_pending_update_statement(
            field,
            update_statement,
            via_path_to_starting_table=via_path_to_starting_table,
        )

    def field_dependency_created(
        self,
        field: Field,
        created_field: Field,
        update_collector: "FieldUpdateCollector",
        field_cache: "FieldCache",
        via_path_to_starting_table: Optional[List[LinkRowField]],
    ):
        old_field = deepcopy(field)
        self._update_formula_after_dependency_change(
            field, old_field, update_collector, field_cache, via_path_to_starting_table
        )

    def field_dependency_updated(
        self,
        field: Field,
        updated_field: Field,
        updated_old_field: Field,
        update_collector: "FieldUpdateCollector",
        field_cache: "FieldCache",
        via_path_to_starting_table: Optional[List[LinkRowField]],
    ):
        old_field = deepcopy(field)

        old_name = updated_old_field.name
        new_name = updated_field.name
        rename = old_name != new_name
        if rename:
            field.formula = FormulaHandler.rename_field_references_in_formula_string(
                field.formula, {old_name: new_name}
            )
        self._update_formula_after_dependency_change(
            field,
            old_field,
            update_collector,
            field_cache,
            via_path_to_starting_table,
        )

    # noinspection PyMethodMayBeStatic
    def _update_formula_after_dependency_change(
        self,
        field: FormulaField,
        old_field: Field,
        update_collector: "FieldUpdateCollector",
        field_cache: "FieldCache",
        via_path_to_starting_table: Optional[List[LinkRowField]],
    ):
        expr = FormulaHandler.recalculate_formula_and_get_update_expression(
            field, old_field, field_cache
        )
        FieldDependencyHandler.rebuild_dependencies(field, field_cache)
        update_collector.add_field_with_pending_update_statement(
            field, expr, via_path_to_starting_table=via_path_to_starting_table
        )
        for (
            dependant_field,
            dependant_field_type,
            path_to_starting_table,
        ) in field.dependant_fields_with_types(field_cache, via_path_to_starting_table):
            dependant_field_type.field_dependency_updated(
                dependant_field,
                field,
                old_field,
                update_collector,
                field_cache,
                path_to_starting_table,
            )

    def field_dependency_deleted(
        self,
        field: Field,
        deleted_field: Field,
        update_collector: "FieldUpdateCollector",
        field_cache: "FieldCache",
        via_path_to_starting_table: Optional[List[LinkRowField]],
    ):
        old_field = deepcopy(field)
        self._update_formula_after_dependency_change(
            field, old_field, update_collector, field_cache, via_path_to_starting_table
        )

    def after_create(self, field, model, user, connection, before, field_kwargs):
        """
        Immediately after the field has been created, we need to populate the values
        with the already existing source_field_name column.
        """

        model = field.table.get_model()
        expr = FormulaHandler.baserow_expression_to_update_django_expression(
            field.cached_typed_internal_expression, model
        )
        model.objects_and_trash.all().update(**{f"{field.db_column}": expr})

    def after_rows_created(
        self,
        field: FormulaField,
        rows: List["GeneratedTableModel"],
        update_collector: "FieldUpdateCollector",
        field_cache: "FieldCache",
    ):
        if field.requires_refresh_after_insert:
            self._refresh_row_values(field, update_collector, field_cache, [])

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
        to_field_kwargs,
    ):
        to_model = to_field.table.get_model()
        expr = FormulaHandler.baserow_expression_to_update_django_expression(
            to_field.cached_typed_internal_expression, to_model
        )
        to_model.objects_and_trash.all().update(**{f"{to_field.db_column}": expr})

    def after_import_serialized(self, field, field_cache):
        field.save(recalculate=True, field_cache=field_cache)
        super().after_import_serialized(field, field_cache)

    def after_rows_imported(
        self,
        field: FormulaField,
        update_collector: "FieldUpdateCollector",
        field_cache: "FieldCache",
        via_path_to_starting_table: Optional[List[LinkRowField]],
    ):
        if field.requires_refresh_after_insert:
            self._refresh_row_values(
                field, update_collector, field_cache, via_path_to_starting_table
            )
        super().after_rows_imported(
            field, update_collector, field_cache, via_path_to_starting_table
        )

    def check_can_order_by(self, field):
        return self.to_baserow_formula_type(field.specific).can_order_by

    def should_backup_field_data_for_same_type_update(
        self, old_field: FormulaField, new_field_attrs: Dict[str, Any]
    ) -> bool:
        return False


class LookupFieldType(FormulaFieldType):
    type = "lookup"
    model_class = LookupField
    api_exceptions_map = {
        **FormulaFieldType.api_exceptions_map,
        InvalidLookupThroughField: ERROR_INVALID_LOOKUP_THROUGH_FIELD,
        InvalidLookupTargetField: ERROR_INVALID_LOOKUP_TARGET_FIELD,
    }
    can_get_unique_values = False
    allowed_fields = BASEROW_FORMULA_TYPE_ALLOWED_FIELDS + [
        "through_field_id",
        "through_field_name",
        "target_field_id",
        "target_field_name",
    ]
    serializer_field_names = BASEROW_FORMULA_TYPE_ALLOWED_FIELDS + [
        "through_field_id",
        "through_field_name",
        "target_field_id",
        "target_field_name",
        "formula_type",
    ]
    serializer_field_overrides = {
        "through_field_name": serializers.CharField(
            required=False,
            allow_blank=True,
            allow_null=True,
            source="through_field.name",
            help_text="The name of the link row field to lookup values for.",
        ),
        "through_field_id": serializers.IntegerField(
            required=False,
            allow_null=True,
            source="through_field.id",
            help_text="The id of the link row field to lookup values for. Will override"
            " the `through_field_name` parameter if both are provided, however only "
            "one is required.",
        ),
        "target_field_name": serializers.CharField(
            required=False,
            allow_blank=True,
            allow_null=True,
            source="target_field.name",
            help_text="The name of the field in the table linked to by the "
            "through_field to lookup.",
        ),
        "target_field_id": serializers.IntegerField(
            required=False,
            allow_null=True,
            source="target_field.id",
            help_text="The id of the field in the table linked to by the "
            "through_field to lookup. Will override the `target_field_id` "
            "parameter if both are provided, however only one is required.",
        ),
        "nullable": serializers.BooleanField(required=False, read_only=True),
    }

    def before_create(
        self, table, primary, allowed_field_values, order, user, field_kwargs
    ):
        self._validate_through_and_target_field_values(
            table,
            allowed_field_values,
        )

    def get_fields_needing_periodic_update(self) -> Optional[QuerySet]:
        return None

    def before_update(self, from_field, to_field_values, user, kwargs):
        if isinstance(from_field, LookupField):
            through_field_id = (
                from_field.through_field.id
                if from_field.through_field is not None
                else None
            )
            target_field_id = (
                from_field.target_field.id
                if from_field.target_field is not None
                else None
            )
            self._validate_through_and_target_field_values(
                from_field.table,
                to_field_values,
                through_field_id,
                target_field_id,
            )
        else:
            self._validate_through_and_target_field_values(
                from_field.table,
                to_field_values,
            )

    def _validate_through_and_target_field_values(
        self,
        table,
        values,
        default_through_field_id=None,
        default_target_field_id=None,
    ):
        through_field_id = values.get("through_field_id", default_through_field_id)
        target_field_id = values.get("target_field_id", default_target_field_id)
        through_field_name = values.get("through_field_name", None)
        target_field_name = values.get("target_field_name", None)

        if through_field_id is None:
            try:
                through_field_id = table.field_set.get(name=through_field_name).id
            except Field.DoesNotExist:
                raise InvalidLookupThroughField()
        try:
            through_field = FieldHandler().get_field(through_field_id, LinkRowField)
        except FieldDoesNotExist:
            # Occurs when the through_field_id points at a non LinkRowField
            raise InvalidLookupThroughField()

        if through_field.table != table:
            raise InvalidLookupThroughField()

        values["through_field_id"] = through_field.id
        values["through_field_name"] = through_field.name

        if target_field_id is None:
            try:
                target_field_id = through_field.link_row_table.field_set.get(
                    name=target_field_name
                ).id
            except Field.DoesNotExist:
                raise InvalidLookupTargetField()

        try:
            target_field = FieldHandler().get_field(target_field_id)
        except FieldDoesNotExist:
            raise InvalidLookupTargetField()

        if target_field.table != through_field.link_row_table:
            raise InvalidLookupTargetField()

        values["target_field_id"] = target_field.id
        values["target_field_name"] = target_field.name

    def field_dependency_updated(
        self,
        field: LookupField,
        updated_field: Field,
        updated_old_field: Field,
        update_collector: "FieldUpdateCollector",
        field_cache: "FieldCache",
        via_path_to_starting_table: Optional[List[LinkRowField]],
    ):
        self._rebuild_field_from_names(field)

        super().field_dependency_updated(
            field,
            updated_field,
            updated_old_field,
            update_collector,
            field_cache,
            via_path_to_starting_table,
        )

    def field_dependency_deleted(
        self,
        field: LookupField,
        deleted_field: Field,
        update_collector: "FieldUpdateCollector",
        field_cache: "FieldCache",
        via_path_to_starting_table: Optional[List[LinkRowField]],
    ):
        self._rebuild_field_from_names(field)

        super().field_dependency_deleted(
            field,
            deleted_field,
            update_collector,
            field_cache,
            via_path_to_starting_table,
        )

    def field_dependency_created(
        self,
        field: LookupField,
        created_field: Field,
        update_collector: "FieldUpdateCollector",
        field_cache: "FieldCache",
        via_path_to_starting_table: Optional[List[LinkRowField]],
    ):
        self._rebuild_field_from_names(field)

        super().field_dependency_created(
            field,
            created_field,
            update_collector,
            field_cache,
            via_path_to_starting_table,
        )

    def _rebuild_field_from_names(self, field):
        values = {
            "through_field_name": field.through_field_name,
            "through_field_id": None,
            "target_field_name": field.target_field_name,
            "target_field_id": None,
        }
        try:
            self._validate_through_and_target_field_values(field.table, values)
        except (InvalidLookupTargetField, InvalidLookupThroughField):
            pass
        for key, value in values.items():
            setattr(field, key, value)
        field.save(recalculate=False)

    def import_serialized(
        self,
        table: "Table",
        serialized_values: Dict[str, Any],
        id_mapping: Dict[str, Any],
    ) -> "Field":
        serialized_copy = serialized_values.copy()
        # The through field and target field id's must be set to None because we
        # don't need them. The field is created based on the field name.
        serialized_copy["through_field_id"] = None
        serialized_copy["target_field_id"] = None
        return super().import_serialized(table, serialized_copy, id_mapping)

    def after_import_serialized(self, field, field_cache):
        self._rebuild_field_from_names(field)
        super().after_import_serialized(field, field_cache)


class MultipleCollaboratorsFieldType(FieldType):
    type = "multiple_collaborators"
    model_class = MultipleCollaboratorsField
    can_get_unique_values = False
    can_be_in_form_view = False

    def get_serializer_field(self, instance, **kwargs):
        required = kwargs.get("required", False)
        field_serializer = CollaboratorSerializer(
            **{
                "required": required,
                "allow_null": False,
                **kwargs,
            }
        )
        return serializers.ListSerializer(
            child=field_serializer, required=required, **kwargs
        )

    def get_internal_value_from_db(
        self, row: "GeneratedTableModel", field_name: str
    ) -> List[int]:
        related_objects = getattr(row, field_name)
        return [{"id": related_object.id} for related_object in related_objects.all()]

    def get_response_serializer_field(self, instance, **kwargs):
        required = kwargs.get("required", False)
        return CollaboratorSerializer(
            **{
                "required": required,
                "allow_null": False,
                "many": True,
                **kwargs,
            }
        )

    def prepare_value_for_db(self, instance, value):
        if value is None:
            return []

        if len(value) == 0:
            return []

        user_ids = [v["id"] for v in value]
        group = instance.table.database.group
        group_users_count = GroupUser.objects.filter(
            user_id__in=user_ids, group_id=group.id
        ).count()

        if group_users_count != len(user_ids):
            raise AllProvidedCollaboratorIdsMustBeValidUsers(user_ids)

        return user_ids

    def prepare_value_for_db_in_bulk(
        self, instance, values_by_row, continue_on_error=False
    ):
        # {user_id -> row_indexes}
        rows_by_value = defaultdict(list)
        all_user_ids = set()
        for row_index, values in values_by_row.items():
            user_ids = [v["id"] for v in values]
            for user_id in user_ids:
                rows_by_value[user_id].append(row_index)
            all_user_ids = all_user_ids.union(user_ids)
            values_by_row[row_index] = user_ids

        group = instance.table.database.group

        selected_ids = GroupUser.objects.filter(
            user_id__in=all_user_ids, group_id=group.id
        ).values_list("user_id", flat=True)

        if len(selected_ids) != len(all_user_ids):
            invalid_ids = sorted(list(all_user_ids - set(selected_ids)))
            if continue_on_error:
                for invalid_id in invalid_ids:
                    for row_index in rows_by_value[invalid_id]:
                        values_by_row[
                            row_index
                        ] = AllProvidedCollaboratorIdsMustBeValidUsers(invalid_id)
            else:
                # or fail fast
                raise AllProvidedCollaboratorIdsMustBeValidUsers(invalid_ids)

        return values_by_row

    def get_serializer_help_text(self, instance):
        return (
            "This field accepts a list of objects representing the chosen "
            "collaborators through the object's `id` property. The id is Baserow "
            "user id. The response objects also contains the collaborator name "
            "directly along with its id."
        )

    def get_export_value(self, value, field_object, rich_value=False):
        if value is None:
            return [] if rich_value else ""
        result = [item.email for item in value.all()]
        if rich_value:
            return result
        else:
            return list_to_comma_separated_string(result)

    def get_human_readable_value(self, value, field_object):
        export_value = self.get_export_value(value, field_object, rich_value=True)
        if len(export_value) == 0:
            return ""
        return ", ".join(export_value)

    def get_model_field(self, instance, **kwargs):
        return None

    def after_model_generation(self, instance, model, field_name, manytomany_models):
        user_meta = type(
            "Meta",
            (AbstractUser.Meta,),
            {
                "managed": False,
                "app_label": model._meta.app_label,
                "db_tablespace": model._meta.db_tablespace,
                "db_table": get_user_model().objects.model._meta.db_table,
                "apps": model._meta.apps,
            },
        )
        user_model = type(
            str(f"MultipleCollaboratorsField{instance.id}User"),
            (AbstractUser,),
            {
                # We need to override the `groups` and `user_permissions` here
                # because they're normally many to many relationships with the
                # `Group` and `Permission` model. This is something that we do not need
                # and we don't want to create reversed relationships for generated
                # model.
                "groups": None,
                "user_permissions": None,
                "Meta": user_meta,
                "__module__": model.__module__,
                "_generated_table_model": True,
            },
        )

        related_name = f"reversed_field_{instance.id}"
        shared_kwargs = {
            "null": True,
            "blank": True,
            "db_table": instance.through_table_name,
            "db_constraint": False,
        }
        additional_filters = {
            "id__in": GroupUser.objects.filter(
                group_id=instance.table.database.group_id
            ).values_list("user_id", flat=True)
        }

        MultipleSelectManyToManyField(
            to=user_model,
            related_name=related_name,
            additional_filters=additional_filters,
            **shared_kwargs,
        ).contribute_to_class(model, field_name)
        MultipleSelectManyToManyField(
            to=model,
            related_name=field_name,
            reversed_additional_filters=additional_filters,
            **shared_kwargs,
        ).contribute_to_class(user_model, related_name)

        # Trigger the newly created pending operations of all the models related to the
        # created CollaboratorField. They need to be called manually because normally
        # they are triggered when a new model is registered. Not triggering them
        # can cause a memory leak because everytime a table model is generated, it will
        # register new pending operations.
        apps = model._meta.apps
        model_field = model._meta.get_field(field_name)
        collaborator_field = user_model._meta.get_field(related_name)
        apps.do_pending_operations(model)
        apps.do_pending_operations(user_model)
        apps.do_pending_operations(model_field.remote_field.through)
        apps.do_pending_operations(model)
        apps.do_pending_operations(collaborator_field.remote_field.through)
        apps.clear_cache()

    def enhance_queryset(self, queryset, field, name):
        return queryset.prefetch_related(name)

    def get_export_serialized_value(self, row, field_name, cache, files_zip, storage):
        cache_entry = f"{field_name}_relations_export"
        if cache_entry not in cache:
            # In order to prevent a lot of lookup queries in the through table, we want
            # to fetch all the relations and add it to a temporary in memory cache
            # containing a mapping of the row ids to collaborator emails.
            cache[cache_entry] = defaultdict(list)
            through_model = row._meta.get_field(field_name).remote_field.through
            through_model_fields = through_model._meta.get_fields()
            current_field_name = through_model_fields[1].name
            relation_field_name = through_model_fields[2].name
            users_relation = through_model.objects.select_related(relation_field_name)
            for relation in users_relation:
                cache[cache_entry][
                    getattr(relation, f"{current_field_name}_id")
                ].append(getattr(relation, relation_field_name).email)
        return cache[cache_entry][row.id]

    def set_import_serialized_value(
        self, row, field_name, value, id_mapping, cache, files_zip, storage
    ):
        group_id = id_mapping["import_group_id"]
        cache_entry = f"{field_name}_relations_import"
        if cache_entry not in cache:
            # In order to prevent a lot of lookup queries in the through table, we want
            # to fetch all the relations and add it to a temporary in memory cache
            # containing a mapping of the row ids to collaborator emails.
            cache[cache_entry] = defaultdict(list)

            groupusers_from_group = GroupUser.objects.filter(
                group_id=group_id
            ).select_related("user")

            for groupuser in groupusers_from_group:
                cache[cache_entry][groupuser.user.email] = groupuser.user.id

        user_ids = []
        for email in value:
            user_id = cache[cache_entry].get(email, None)
            if user_id is not None:
                user_ids.append(user_id)

        getattr(row, field_name).set(user_ids)

    def random_value(self, instance, fake, cache):
        """
        Selects a random sublist out of the possible collaborators.
        """

        cache_entry_name = f"field_{instance.id}_collaborators"

        if cache_entry_name not in cache:
            table = Table.objects.get(id=instance.table_id)
            groupusers_from_group = GroupUser.objects.filter(
                group=table.database.group
            ).select_related("user")
            cache[cache_entry_name] = [
                groupuser.user for groupuser in groupusers_from_group
            ]

        collaborators = cache[cache_entry_name]

        if not collaborators:
            return None

        random_choice = randint(1, len(collaborators))  # nosec

        return sample(set([x.id for x in collaborators]), random_choice)

    def get_order(self, field, field_name, order_direction):
        """
        If the user wants to sort the results he expects them to be ordered
        alphabetically based on the user's name and not in the id which is
        stored in the table. This method generates a Case expression which maps
        the id to the correct position.
        """

        sort_column_name = f"{field_name}_agg_sort"
        query = Coalesce(StringAgg(f"{field_name}__first_name", ""), Value(""))
        annotation = {sort_column_name: query}

        order = F(sort_column_name)
        if order_direction == "DESC":
            order = order.desc(nulls_first=True)
        else:
            order = order.asc(nulls_first=True)

        return AnnotatedOrder(annotation=annotation, order=order)

    def get_value_for_filter(self, row: "GeneratedTableModel", field_name: str) -> any:
        related_objects = getattr(row, field_name)
        values = [related_object.first_name for related_object in related_objects.all()]
        return list_to_comma_separated_string(values)
