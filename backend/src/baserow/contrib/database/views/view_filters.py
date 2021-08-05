from datetime import datetime
from decimal import Decimal
from math import floor, ceil

from dateutil import parser
from dateutil.parser import ParserError
from django.contrib.postgres.fields import JSONField
from django.db.models import Q, IntegerField, BooleanField, DateTimeField
from django.db.models.fields.related import ManyToManyField, ForeignKey
from pytz import timezone, all_timezones

from baserow.contrib.database.fields.field_filters import (
    filename_contains_filter,
    OptionallyAnnotatedQ,
)
from baserow.contrib.database.fields.field_types import (
    TextFieldType,
    LongTextFieldType,
    URLFieldType,
    NumberFieldType,
    DateFieldType,
    LinkRowFieldType,
    BooleanFieldType,
    EmailFieldType,
    FileFieldType,
    SingleSelectFieldType,
    PhoneNumberFieldType,
)
from baserow.contrib.database.fields.registries import field_type_registry

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

    type = "equal"
    compatible_field_types = [
        TextFieldType.type,
        LongTextFieldType.type,
        URLFieldType.type,
        NumberFieldType.type,
        BooleanFieldType.type,
        EmailFieldType.type,
        PhoneNumberFieldType.type,
    ]

    def get_filter(self, field_name, value, model_field, field):
        value = value.strip()

        # If an empty value has been provided we do not want to filter at all.
        if value == "":
            return Q()

        # Check if the model_field accepts the value.
        try:
            model_field.get_prep_value(value)
            return Q(**{field_name: value})
        except Exception:
            pass

        return Q()


class NotEqualViewFilterType(NotViewFilterTypeMixin, EqualViewFilterType):
    type = "not_equal"


class FilenameContainsViewFilterType(ViewFilterType):
    """
    The filename contains filter checks if the filename's visible name contains the
    provided filter value. It is only compatible with fields.JSONField which contain
    a list of File JSON Objects.
    """

    type = "filename_contains"
    compatible_field_types = [FileFieldType.type]

    def get_filter(self, *args):
        return filename_contains_filter(*args)


class ContainsViewFilterType(ViewFilterType):
    """
    The contains filter checks if the field value contains the provided filter value.
    It is compatible with models.CharField and models.TextField.
    """

    type = "contains"
    compatible_field_types = [
        TextFieldType.type,
        LongTextFieldType.type,
        URLFieldType.type,
        EmailFieldType.type,
        PhoneNumberFieldType.type,
        DateFieldType.type,
        SingleSelectFieldType.type,
        NumberFieldType.type,
    ]

    def get_filter(self, field_name, value, model_field, field) -> OptionallyAnnotatedQ:
        field_type = field_type_registry.get_by_model(field)
        return field_type.contains_query(field_name, value, model_field, field)


class ContainsNotViewFilterType(NotViewFilterTypeMixin, ContainsViewFilterType):
    type = "contains_not"


class HigherThanViewFilterType(ViewFilterType):
    """
    The higher than filter checks if the field value is higher than the filter value.
    It only works if a numeric number is provided. It is at compatible with
    models.IntegerField and models.DecimalField.
    """

    type = "higher_than"
    compatible_field_types = [NumberFieldType.type]

    def get_filter(self, field_name, value, model_field, field):
        value = value.strip()

        # If an empty value has been provided we do not want to filter at all.
        if value == "":
            return Q()

        if isinstance(model_field, IntegerField) and value.find(".") != -1:
            decimal = Decimal(value)
            value = floor(decimal)

        # Check if the model_field accepts the value.
        try:
            model_field.get_prep_value(value)
            return Q(**{f"{field_name}__gt": value})
        except Exception:
            pass

        return Q()


class LowerThanViewFilterType(ViewFilterType):
    """
    The lower than filter checks if the field value is lower than the filter value.
    It only works if a numeric number is provided. It is at compatible with
    models.IntegerField and models.DecimalField.
    """

    type = "lower_than"
    compatible_field_types = [NumberFieldType.type]

    def get_filter(self, field_name, value, model_field, field):
        value = value.strip()

        # If an empty value has been provided we do not want to filter at all.
        if value == "":
            return Q()

        if isinstance(model_field, IntegerField) and value.find(".") != -1:
            decimal = Decimal(value)
            value = ceil(decimal)

        # Check if the model_field accepts the value.
        try:
            model_field.get_prep_value(value)
            return Q(**{f"{field_name}__lt": value})
        except Exception:
            pass

        return Q()


class DateEqualViewFilterType(ViewFilterType):
    """
    The date filter parses the provided value as date and checks if the field value is
    the same date. It only works if a valid ISO date is provided as value and it is
    only compatible with models.DateField and models.DateTimeField.
    """

    type = "date_equal"
    compatible_field_types = [DateFieldType.type]

    def get_filter(self, field_name, value, model_field, field):
        """
        Parses the provided value string and converts it to an aware datetime object.
        That object will used to make a comparison with the provided field name.
        """

        value = value.strip()

        if value == "":
            return Q()

        utc = timezone("UTC")

        try:
            datetime = parser.isoparse(value).astimezone(utc)
        except (ParserError, ValueError):
            return Q()

        # If the length if string value is lower than 10 characters we know it is only
        # a date so we can match only on year, month and day level. This way if a date
        # is provided, but if it tries to compare with a models.DateTimeField it will
        # still give back accurate results.
        if len(value) <= 10:
            return Q(
                **{
                    f"{field_name}__year": datetime.year,
                    f"{field_name}__month": datetime.month,
                    f"{field_name}__day": datetime.day,
                }
            )
        else:
            return Q(**{field_name: datetime})


class BaseDateFieldLookupFilterType(ViewFilterType):
    """
    The base date field lookup filter serves as a base class for DateViewFilters.
    With it a valid ISO date can be parsed into a date object which subsequently can
    be used to filter a model.DateField or model.DateTimeField.
    If the model field in question is a DateTimeField then the get_filter function
    makes sure to only use the date part of the datetime in order to filter. This means
    that the time part of a DateTimeField gets completely ignored.

    The 'query_field_lookup' needs to be set on the deriving classes to something like
    '__lt'
    '__lte'
    '__gt'
    '__gte'
    """

    type = "base_date_field_lookup_type"
    query_field_lookup = ""
    compatible_field_types = [DateFieldType.type]

    @staticmethod
    def parse_date(value: str) -> datetime.date:
        """
        Parses the provided value string and converts it to a date object.
        Raises an error if the provided value is an empty string or cannot be parsed
        to a date object
        """
        value = value.strip()

        if value == "":
            raise ValueError

        try:
            parsed_date = parser.isoparse(value).date()
            return parsed_date
        except ValueError as e:
            raise e

    def get_filter(self, field_name, value, model_field, field):
        # in order to only compare the date part of a datetime field
        # we need to verify that we are in fact dealing with a datetime field
        # if so the django query lookup '__date' gets appended to the field_name
        # otherwise (i.e. it is a date field) nothing gets appended
        query_date_lookup = ""
        if isinstance(model_field, DateTimeField):
            query_date_lookup = "__date"
        try:
            parsed_date = self.parse_date(value)
            field_key = f"{field_name}{query_date_lookup}{self.query_field_lookup}"
            return Q(**{field_key: parsed_date})
        except (ParserError, ValueError):
            return Q()


class DateBeforeViewFilterType(BaseDateFieldLookupFilterType):
    """
    The date before filter parses the provided filter value as date and checks if the
    field value is before this date (lower than).
    It is an extension of the BaseDateFieldLookupFilter
    """

    type = "date_before"
    query_field_lookup = "__lt"
    compatible_field_types = [DateFieldType.type]


class DateAfterViewFilterType(BaseDateFieldLookupFilterType):
    """
    The after date filter parses the provided filter value as date and checks if
    the field value is after this date (greater than).
    It is an extension of the BaseDateFieldLookupFilter
    """

    type = "date_after"
    query_field_lookup = "__gt"


class DateEqualsTodayViewFilterType(ViewFilterType):
    """
    The today filter checks if the field value matches with today's date.
    """

    type = "date_equals_today"
    compatible_field_types = [DateFieldType.type]
    query_for = ["year", "month", "day"]

    def get_filter(self, field_name, value, model_field, field):
        timezone_string = value if value in all_timezones else "UTC"
        timezone_object = timezone(timezone_string)
        now = datetime.utcnow().astimezone(timezone_object)
        query_dict = dict()
        if "year" in self.query_for:
            query_dict[f"{field_name}__year"] = now.year
        if "month" in self.query_for:
            query_dict[f"{field_name}__month"] = now.month
        if "day" in self.query_for:
            query_dict[f"{field_name}__day"] = now.day
        return Q(**query_dict)


class DateEqualsCurrentMonthViewFilterType(DateEqualsTodayViewFilterType):
    """
    The current month filter works as a subset of today filter and checks if the
    field value falls into current month.
    """

    type = "date_equals_month"
    query_for = ["year", "month"]


class DateEqualsCurrentYearViewFilterType(DateEqualsTodayViewFilterType):
    """
    The current month filter works as a subset of today filter and checks if the
    field value falls into current year.
    """

    type = "date_equals_year"
    query_for = ["year"]


class DateNotEqualViewFilterType(NotViewFilterTypeMixin, DateEqualViewFilterType):
    type = "date_not_equal"


class SingleSelectEqualViewFilterType(ViewFilterType):
    """
    The single select equal filter accepts a select option id as filter value. This
    filter is only compatible with the SingleSelectFieldType field type.
    """

    type = "single_select_equal"
    compatible_field_types = [SingleSelectFieldType.type]

    def get_filter(self, field_name, value, model_field, field):
        value = value.strip()

        if value == "":
            return Q()

        try:
            int(value)
            return Q(**{f"{field_name}_id": value})
        except Exception:
            return Q()

    def set_import_serialized_value(self, value, id_mapping):
        try:
            value = int(value)
        except ValueError:
            return ""

        return str(id_mapping["database_field_select_options"].get(value, ""))


class SingleSelectNotEqualViewFilterType(
    NotViewFilterTypeMixin, SingleSelectEqualViewFilterType
):
    type = "single_select_not_equal"


class BooleanViewFilterType(ViewFilterType):
    """
    The boolean filter tries to convert the provided filter value to a boolean and
    compares that to the field value. If for example '1' is provided then only field
    value with True are going to be matched. This filter is compatible with
    models.BooleanField.
    """

    type = "boolean"
    compatible_field_types = [BooleanFieldType.type]

    def get_filter(self, field_name, value, model_field, field):
        value = value.strip().lower()
        value = value in [
            "y",
            "t",
            "o",
            "yes",
            "true",
            "on",
            "1",
        ]

        # Check if the model_field accepts the value.
        try:
            model_field.get_prep_value(value)
            return Q(**{field_name: value})
        except Exception:
            pass

        return Q()


class LinkRowHasViewFilterType(ViewFilterType):
    """
    The link row has filter accepts the row ID of the related table as value. It
    filters the queryset so that only rows that have a relationship with the provided
    row ID will remain. So if for example '10' is provided, then only rows where the
    link row field has a relationship with the row '10' persists.
    """

    type = "link_row_has"
    compatible_field_types = [LinkRowFieldType.type]

    def get_filter(self, field_name, value, model_field, field):
        value = value.strip()

        try:
            return Q(**{f"{field_name}__in": [int(value)]})
        except ValueError:
            return Q()

    def get_preload_values(self, view_filter):
        """
        This method preloads the display name of the related value. This prevents a
        lot of API requests if the view has a lot of `link_row_has` filters. It will
        also make sure that the display name is visible for read only previews.
        """

        name = None
        related_row_id = None

        try:
            related_row_id = int(view_filter.value)
        except ValueError:
            pass

        if related_row_id:
            field = view_filter.field.specific
            table = field.link_row_table
            primary_field = table.field_set.get(primary=True)
            model = table.get_model(field_ids=[], fields=[primary_field])

            try:
                name = str(model.objects.get(pk=related_row_id))
            except model.DoesNotExist:
                pass

        return {"display_name": name}


class LinkRowHasNotViewFilterType(NotViewFilterTypeMixin, LinkRowHasViewFilterType):
    """
    The link row has filter accepts the row ID of the related table as value. It
    filters the queryset so that only rows that don't have a relationship with the
    provided row ID will remain. So if for example '10' is provided, then only rows
    where the link row field does not have a relationship with the row '10' persists.
    """

    type = "link_row_has_not"


class EmptyViewFilterType(ViewFilterType):
    """
    The empty filter checks if the field value is empty, this can be '', null,
    [] or anything. It is compatible with all fields
    """

    type = "empty"
    compatible_field_types = [
        TextFieldType.type,
        LongTextFieldType.type,
        URLFieldType.type,
        NumberFieldType.type,
        BooleanFieldType.type,
        DateFieldType.type,
        LinkRowFieldType.type,
        EmailFieldType.type,
        FileFieldType.type,
        SingleSelectFieldType.type,
        PhoneNumberFieldType.type,
    ]

    def get_filter(self, field_name, value, model_field, field):
        # If the model_field is a ManyToMany field we only have to check if it is None.
        if isinstance(model_field, ManyToManyField) or isinstance(
            model_field, ForeignKey
        ):
            return Q(**{f"{field_name}": None})

        if isinstance(model_field, BooleanField):
            return Q(**{f"{field_name}": False})

        q = Q(**{f"{field_name}__isnull": True})
        q.add(Q(**{f"{field_name}": None}), Q.OR)

        if isinstance(model_field, JSONField):
            q.add(Q(**{f"{field_name}": []}), Q.OR)
            q.add(Q(**{f"{field_name}": {}}), Q.OR)

        # If the model field accepts an empty string as value we are going to add
        # that to the or statement.
        try:
            model_field.get_prep_value("")
            q.add(Q(**{f"{field_name}": ""}), Q.OR)
        except Exception:
            pass

        return q


class NotEmptyViewFilterType(NotViewFilterTypeMixin, EmptyViewFilterType):
    type = "not_empty"
