from datetime import datetime, time, timedelta
from decimal import Decimal
from math import ceil, floor
from typing import Dict, Union

from django.contrib.postgres.aggregates.general import ArrayAgg
from django.db.models import DateTimeField, IntegerField, Q
from django.db.models.functions import Cast, Length

from dateutil import parser
from dateutil.parser import ParserError
from dateutil.relativedelta import relativedelta
from pytz import all_timezones, timezone

from baserow.contrib.database.fields.field_filters import (
    FILTER_TYPE_AND,
    AnnotatedQ,
    FilterBuilder,
    OptionallyAnnotatedQ,
    filename_contains_filter,
)
from baserow.contrib.database.fields.field_types import (
    BooleanFieldType,
    CreatedOnFieldType,
    DateFieldType,
    EmailFieldType,
    FileFieldType,
    FormulaFieldType,
    LastModifiedFieldType,
    LinkRowFieldType,
    LongTextFieldType,
    MultipleCollaboratorsFieldType,
    MultipleSelectFieldType,
    NumberFieldType,
    PhoneNumberFieldType,
    RatingFieldType,
    SingleSelectFieldType,
    TextFieldType,
    URLFieldType,
)
from baserow.contrib.database.fields.registries import field_type_registry
from baserow.contrib.database.formula import (
    BaserowFormulaBooleanType,
    BaserowFormulaCharType,
    BaserowFormulaDateType,
    BaserowFormulaNumberType,
    BaserowFormulaTextType,
)
from baserow.core.expressions import Timezone

from .registries import ViewFilterType


class NotViewFilterTypeMixin:
    def default_filter_on_exception(self):
        return Q()

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
        RatingFieldType.type,
        EmailFieldType.type,
        PhoneNumberFieldType.type,
        FormulaFieldType.compatible_with_formula_types(
            BaserowFormulaTextType.type,
            BaserowFormulaCharType.type,
            BaserowFormulaNumberType.type,
        ),
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
            return self.default_filter_on_exception()


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


class HasFileTypeViewFilterType(ViewFilterType):
    """
    The file field type column contains an array of objects with details related to
    the uploaded user files. Every object always contains the property `is_image`
    that indicates if the user file is an image. Using the Django contains lookup,
    we can check if there is at least one object where the `is_image` is True. If the
    filter value is `image`, there must at least be one object where the `is_image`
    is true. If the filter value is `document` there must at least be one object
    where the `is_image` is false. If an unsupported filter value is provided, we don't
    want to filter on anything.
    """

    type = "has_file_type"
    compatible_field_types = [FileFieldType.type]

    def get_filter(self, field_name, value, model_field, field):
        value = value.strip()
        is_image = value == "image"
        is_document = value == "document"

        if is_document or is_image:
            return Q(**{f"{field_name}__contains": [{"is_image": is_image}]})
        else:
            return Q()


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
        LastModifiedFieldType.type,
        CreatedOnFieldType.type,
        SingleSelectFieldType.type,
        MultipleSelectFieldType.type,
        NumberFieldType.type,
        FormulaFieldType.compatible_with_formula_types(
            BaserowFormulaTextType.type,
            BaserowFormulaCharType.type,
            BaserowFormulaNumberType.type,
            BaserowFormulaDateType.type,
        ),
    ]

    def get_filter(self, field_name, value, model_field, field) -> OptionallyAnnotatedQ:
        # Check if the model_field accepts the value.
        try:
            field_type = field_type_registry.get_by_model(field)
            return field_type.contains_query(field_name, value, model_field, field)
        except Exception:
            return self.default_filter_on_exception()


class ContainsNotViewFilterType(NotViewFilterTypeMixin, ContainsViewFilterType):
    type = "contains_not"


class LengthIsLowerThanViewFilterType(ViewFilterType):
    """
    The length is lower than filter checks if the fields character
    length is less than x
    """

    type = "length_is_lower_than"
    compatible_field_types = [
        TextFieldType.type,
        LongTextFieldType.type,
        URLFieldType.type,
        EmailFieldType.type,
        PhoneNumberFieldType.type,
    ]

    def get_filter(self, field_name, value, model_field, field):
        if value == 0:
            return Q()

        try:
            return AnnotatedQ(
                annotation={f"{field_name}_len": Length(field_name)},
                q={f"{field_name}_len__lt": int(value)},
            )
        except ValueError:
            return self.default_filter_on_exception()


class HigherThanViewFilterType(ViewFilterType):
    """
    The higher than filter checks if the field value is higher than the filter value.
    It only works if a numeric number is provided. It is at compatible with
    models.IntegerField and models.DecimalField.
    """

    type = "higher_than"
    compatible_field_types = [
        NumberFieldType.type,
        RatingFieldType.type,
        FormulaFieldType.compatible_with_formula_types(
            BaserowFormulaNumberType.type,
        ),
    ]

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
            return self.default_filter_on_exception()


class LowerThanViewFilterType(ViewFilterType):
    """
    The lower than filter checks if the field value is lower than the filter value.
    It only works if a numeric number is provided. It is at compatible with
    models.IntegerField and models.DecimalField.
    """

    type = "lower_than"
    compatible_field_types = [
        NumberFieldType.type,
        RatingFieldType.type,
        FormulaFieldType.compatible_with_formula_types(
            BaserowFormulaNumberType.type,
        ),
    ]

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
            return self.default_filter_on_exception()


class DateEqualViewFilterType(ViewFilterType):
    """
    The date filter parses the provided value as date and checks if the field value is
    the same date. It only works if a valid ISO date is provided as value and it is
    only compatible with models.DateField and models.DateTimeField.
    """

    type = "date_equal"
    compatible_field_types = [
        DateFieldType.type,
        LastModifiedFieldType.type,
        CreatedOnFieldType.type,
        FormulaFieldType.compatible_with_formula_types(
            BaserowFormulaDateType.type,
        ),
    ]

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
            parsed_datetime = parser.isoparse(value).astimezone(utc)
        except (ParserError, ValueError):
            return Q()

        # If the length of the string value is lower than 10 characters we know it is
        # only a date so we can match only on year, month and day level. This way if a
        # date is provided, but if it tries to compare with a models.DateTimeField it
        # will still give back accurate results.
        # Since the LastModified and CreateOn fields are stored for a specific timezone
        # we need to make sure to take this timezone into account when comparing to
        # the "equals_date"
        has_timezone = hasattr(field, "timezone")
        if len(value) <= 10:

            def query_dict(query_field_name):
                return {
                    f"{query_field_name}__year": parsed_datetime.year,
                    f"{query_field_name}__month": parsed_datetime.month,
                    f"{query_field_name}__day": parsed_datetime.day,
                }

            if has_timezone:
                timezone_string = field.get_timezone()
                tmp_field_name = f"{field_name}_timezone_{timezone_string}"
                return AnnotatedQ(
                    annotation={
                        f"{tmp_field_name}": Timezone(field_name, timezone_string)
                    },
                    q=query_dict(tmp_field_name),
                )
            else:
                return Q(**query_dict(field_name))
        else:
            return Q(**{field_name: parsed_datetime})


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
    query_date_lookup = ""
    compatible_field_types = [
        DateFieldType.type,
        LastModifiedFieldType.type,
        CreatedOnFieldType.type,
        FormulaFieldType.compatible_with_formula_types(
            BaserowFormulaDateType.type,
        ),
    ]

    @staticmethod
    def parse_date(value: str) -> Union[datetime.date, datetime]:
        """
        Parses the provided value string and converts it to a date object.
        Raises an error if the provided value is an empty string or cannot be parsed
        to a date object
        """

        value = value.strip()

        if value == "":
            raise ValueError

        utc = timezone("UTC")

        try:
            parsed_datetime = parser.isoparse(value).astimezone(utc)
            return parsed_datetime
        except ValueError as e:
            raise e

    @staticmethod
    def is_date(value: str) -> bool:
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def get_filter(self, field_name, value, model_field, field):
        # in order to only compare the date part of a datetime field
        # we need to verify that we are in fact dealing with a datetime field
        # if so the django query lookup '__date' gets appended to the field_name
        # otherwise (i.e. it is a date field) nothing gets appended
        query_date_lookup = self.query_date_lookup
        if (
            isinstance(model_field, DateTimeField)
            and self.is_date(value)
            and not query_date_lookup
        ):
            query_date_lookup = "__date"
        try:
            parsed_date = self.parse_date(value)
            has_timezone = hasattr(field, "timezone")
            field_key = f"{field_name}{query_date_lookup}{self.query_field_lookup}"
            if has_timezone:
                timezone_string = field.get_timezone()
                tmp_field_name = f"{field_name}_timezone_{timezone_string}"
                field_key = (
                    f"{tmp_field_name}{query_date_lookup}{self.query_field_lookup}"
                )

                return AnnotatedQ(
                    annotation={
                        f"{tmp_field_name}": Timezone(field_name, timezone_string)
                    },
                    q={field_key: parsed_date},
                )
            else:
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


class DateAfterViewFilterType(BaseDateFieldLookupFilterType):
    """
    The after date filter parses the provided filter value as date and checks if
    the field value is after this date (greater than).
    It is an extension of the BaseDateFieldLookupFilter
    """

    type = "date_after"
    query_field_lookup = "__gt"


class DateCompareTodayViewFilterType(ViewFilterType):
    """
    The today filter checks if the field value matches the defined operator with
    today's date.
    """

    @property
    def type(self) -> str:
        """
        Returns the type of the filter (e.g. 'date_equals_today' for a
        view_filter that filters for today).
        """

        raise NotImplementedError

    def make_query_dict(self, field_name: str, now: datetime) -> Dict:
        """
        Creates a query dict for the specific view_filter, given the field name
        based on today's date.

        :param field_name: The field name to use in the query dict.
        :param now: The current date.
        :return: The query dict.
        """

        raise NotImplementedError

    compatible_field_types = [
        DateFieldType.type,
        LastModifiedFieldType.type,
        CreatedOnFieldType.type,
        FormulaFieldType.compatible_with_formula_types(
            BaserowFormulaDateType.type,
        ),
    ]

    def get_filter(self, field_name, value, model_field, field):
        timezone_string = value if value in all_timezones else "UTC"
        timezone_object = timezone(timezone_string)
        field_has_timezone = hasattr(field, "timezone")
        now = datetime.utcnow().astimezone(timezone_object)

        if field_has_timezone:
            tmp_field_name = f"{field_name}_timezone_{timezone_string}"
            return AnnotatedQ(
                annotation={f"{tmp_field_name}": Timezone(field_name, timezone_string)},
                q=self.make_query_dict(tmp_field_name, now),
            )
        else:
            return Q(**self.make_query_dict(field_name, now))


class DateEqualsTodayViewFilterType(DateCompareTodayViewFilterType):
    """
    The today filter checks if the field value matches with today's date.
    """

    type = "date_equals_today"

    def make_query_dict(self, field_name, now):
        return {
            f"{field_name}__day": now.day,
            f"{field_name}__month": now.month,
            f"{field_name}__year": now.year,
        }


class DateBeforeTodayViewFilterType(DateCompareTodayViewFilterType):
    """
    The before today filter checks if the field value is before today's date.
    """

    type = "date_before_today"

    def make_query_dict(self, field_name, now):
        min_today = datetime.combine(now, time.min)
        return {f"{field_name}__lt": min_today}


class DateAfterTodayViewFilterType(DateCompareTodayViewFilterType):
    """
    The after today filter checks if the field value is after today's date.
    """

    type = "date_after_today"

    def make_query_dict(self, field_name, now):
        max_today = datetime.combine(now, time.max)
        return {f"{field_name}__gt": max_today}


class DateEqualsXAgoViewFilterType(ViewFilterType):
    """
    Base class for is days, months, years ago filter.
    """

    query_for = ["year", "month", "day"]

    compatible_field_types = [
        DateFieldType.type,
        LastModifiedFieldType.type,
        CreatedOnFieldType.type,
        FormulaFieldType.compatible_with_formula_types(
            BaserowFormulaDateType.type,
        ),
    ]

    def _extract_values(self, value, separator="?"):
        try:
            tzone, time_unit_ago = value.split(separator)
            time_unit_ago = int(time_unit_ago)
        except ValueError:
            return None, None

        timezone_string = tzone if tzone in all_timezones else "UTC"
        return timezone_string, time_unit_ago

    def get_date_to_compare(now: datetime, x_units_ago: int) -> datetime:
        """
        Should be overriden in subclasses and return computed date
        that will be used to compare year, month and day portions
        in get_filter.

        :param now: Datetime in the specified timezone.
        :param x_units_ago: Number of days/months/years that the
            date needs to shift in the past.
        """

        raise NotImplementedError(
            "Each subclass must have its own get_date_to_compare method."
        )

    def get_filter(self, field_name, value, model_field, field):
        timezone_string, x_units_ago = self._extract_values(value)
        if x_units_ago is None:
            # invalid x_units_ago value will result in an empty filter
            return Q()

        timezone_object = timezone(timezone_string)
        field_has_timezone = hasattr(field, "timezone")
        now = datetime.utcnow().astimezone(timezone_object)
        try:
            when = self.get_date_to_compare(now, x_units_ago)
        except Exception:
            # return nothing when the filter can't be computed
            return Q(pk__in=[])

        def make_query_dict(query_field_name):
            query_dict = dict()
            if "year" in self.query_for:
                query_dict[f"{query_field_name}__year"] = when.year
            if "month" in self.query_for:
                query_dict[f"{query_field_name}__month"] = when.month
            if "day" in self.query_for:
                query_dict[f"{query_field_name}__day"] = when.day

            return query_dict

        if field_has_timezone:
            tmp_field_name = f"{field_name}_timezone_{timezone_string}"
            return AnnotatedQ(
                annotation={f"{tmp_field_name}": Timezone(field_name, timezone_string)},
                q=make_query_dict(tmp_field_name),
            )
        else:
            return Q(**make_query_dict(field_name))


class DateEqualsDaysAgoViewFilterType(DateEqualsXAgoViewFilterType):
    """
    The "number of days ago" filter checks if the field value matches with today's
    date minus the specified number of days.

    The value of the filter is expected to be a string like "Europe/Rome?1".
    It uses character ? as separator between the timezone and the number of days.
    """

    type = "date_equals_days_ago"

    def get_date_to_compare(self, now, x_units_ago):
        return now - timedelta(days=x_units_ago)


class DateEqualsMonthsAgoViewFilterType(DateEqualsXAgoViewFilterType):
    """
    The "number of months ago" filter checks if the field value's month is within
    the specified "months ago" based on the current date.

    The value of the filter is expected to be a string like "Europe/Rome?1".
    It uses character ? as separator between the timezone and the number of months.
    """

    type = "date_equals_months_ago"
    query_for = ["year", "month"]

    def get_date_to_compare(self, now, x_units_ago):
        return now + relativedelta(months=-x_units_ago)


class DateEqualsYearsAgoViewFilterType(DateEqualsXAgoViewFilterType):
    """
    The "is years ago" filter checks if the field value's year is within
    the specified "years ago" based on the current date.

    The value of the filter is expected to be a string like "Europe/Rome?1".
    It uses character ? as separator between the timezone and the number of months.
    """

    type = "date_equals_years_ago"
    query_for = ["year"]

    def get_date_to_compare(self, now, x_units_ago):
        return now + relativedelta(years=-x_units_ago)


class DateEqualsCurrentWeekViewFilterType(DateCompareTodayViewFilterType):
    """
    The current week filter works as a subset of today filter and checks if the
    field value falls into current week.
    """

    type = "date_equals_week"

    def make_query_dict(self, field_name, now):
        week_of_year = now.isocalendar()[1]
        return {
            f"{field_name}__week": week_of_year,
            f"{field_name}__year": now.year,
        }


class DateEqualsCurrentMonthViewFilterType(DateCompareTodayViewFilterType):
    """
    The current month filter works as a subset of today filter and checks if the
    field value falls into current month.
    """

    type = "date_equals_month"

    def make_query_dict(self, field_name, now):
        return {
            f"{field_name}__month": now.month,
            f"{field_name}__year": now.year,
        }


class DateEqualsCurrentYearViewFilterType(DateCompareTodayViewFilterType):
    """
    The current month filter works as a subset of today filter and checks if the
    field value falls into current year.
    """

    type = "date_equals_year"

    def make_query_dict(self, field_name, now):
        return {
            f"{field_name}__year": now.year,
        }


class DateNotEqualViewFilterType(NotViewFilterTypeMixin, DateEqualViewFilterType):
    type = "date_not_equal"


class DateEqualsDayOfMonthViewFilterType(BaseDateFieldLookupFilterType):
    """
    The day of month filter checks if the field number value
    matches the date's day of the month value.
    """

    type = "date_equals_day_of_month"
    query_date_lookup = "__day"

    @staticmethod
    def parse_date(value: str) -> str:
        # Check if the value is a positive number
        if not value.isdigit():
            raise ValueError

        # Check if the value is a valid day of the month
        if int(value) < 1 or int(value) > 31:
            raise ValueError

        return value


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
    compatible_field_types = [
        BooleanFieldType.type,
        FormulaFieldType.compatible_with_formula_types(
            BaserowFormulaBooleanType.type,
        ),
    ]

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
        # noinspection PyBroadException
        try:
            model_field.get_prep_value(value)
            return Q(**{field_name: value})
        except Exception:
            return Q()


class ManyToManyHasBaseViewFilter(ViewFilterType):
    """
    The many to many base filter accepts an relationship ID. It filters the queryset so
    that only rows that have a relationship with the provided ID will remain. So if for
    example '10' is provided, then only rows where the many to many field has a
    relationship to a foreignkey with the ID of 10.
    """

    def get_filter(self, field_name, value, model_field, field):
        value = value.strip()

        try:
            # We annotate the queryset with an aggregated Array containing all the ids
            # of the related field. Then we filter on this annotated column by checking
            # which of the items in the array overlap with a new Array containing the
            # value of the filter. That way we can make sure that chaining more than
            # one filter works correctly.
            return AnnotatedQ(
                annotation={
                    f"{field_name}_array": ArrayAgg(Cast(field_name, IntegerField())),
                },
                q={f"{field_name}_array__overlap": [int(value)]},
            )
        except ValueError:
            return Q()


class LinkRowHasViewFilterType(ManyToManyHasBaseViewFilter):
    """
    The link row has filter accepts the row ID of the related table as value.
    """

    type = "link_row_has"
    compatible_field_types = [LinkRowFieldType.type]

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
            model = table.get_model(
                field_ids=[], fields=[primary_field], add_dependencies=False
            )

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


class LinkRowContainsViewFilterType(ViewFilterType):
    type = "link_row_contains"
    compatible_field_types = [LinkRowFieldType.type]

    def get_filter(self, field_name, value, model_field, field) -> OptionallyAnnotatedQ:
        related_primary_field = field.get_related_primary_field().specific
        related_primary_field_type = field_type_registry.get_by_model(
            related_primary_field
        )
        model = field.table.get_model()
        related_primary_field_model_field = related_primary_field_type.get_model_field(
            related_primary_field
        )

        subquery = (
            FilterBuilder(FILTER_TYPE_AND)
            .filter(
                related_primary_field_type.contains_query(
                    f"{field_name}__{related_primary_field.db_column}",
                    value,
                    related_primary_field_model_field,
                    related_primary_field,
                )
            )
            .apply_to_queryset(model.objects)
            .values_list("id", flat=True)
        )

        return Q(
            **{f"id__in": subquery},
        )


class LinkRowNotContainsViewFilterType(
    NotViewFilterTypeMixin, LinkRowContainsViewFilterType
):
    type = "link_row_not_contains"

    def get_filter(self, field_name, value, model_field, field) -> OptionallyAnnotatedQ:
        if value == "":
            return Q()

        return super().get_filter(field_name, value, model_field, field)


class MultipleSelectHasViewFilterType(ManyToManyHasBaseViewFilter):
    """
    The multiple select has filter accepts the ID of the select_option to filter for
    and filters the rows where the multiple select field has the provided select_option.
    """

    type = "multiple_select_has"
    compatible_field_types = [MultipleSelectFieldType.type]

    def set_import_serialized_value(self, value, id_mapping):
        try:
            value = int(value)
        except ValueError:
            return ""

        return str(id_mapping["database_field_select_options"].get(value, ""))


class MultipleSelectHasNotViewFilterType(
    NotViewFilterTypeMixin, MultipleSelectHasViewFilterType
):
    """
    The multiple select has filter accepts the ID of the select_option to filter for
    and filters the rows where the multiple select field does not have the provided
    select_option.
    """

    type = "multiple_select_has_not"


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
        RatingFieldType.type,
        BooleanFieldType.type,
        DateFieldType.type,
        LastModifiedFieldType.type,
        CreatedOnFieldType.type,
        LinkRowFieldType.type,
        EmailFieldType.type,
        FileFieldType.type,
        SingleSelectFieldType.type,
        PhoneNumberFieldType.type,
        MultipleSelectFieldType.type,
        MultipleCollaboratorsFieldType.type,
        FormulaFieldType.compatible_with_formula_types(
            BaserowFormulaTextType.type,
            BaserowFormulaCharType.type,
            BaserowFormulaNumberType.type,
            BaserowFormulaDateType.type,
            BaserowFormulaBooleanType.type,
        ),
    ]

    def get_filter(self, field_name, value, model_field, field):
        field_type = field_type_registry.get_by_model(field)

        return field_type.empty_query(field_name, model_field, field)


class NotEmptyViewFilterType(NotViewFilterTypeMixin, EmptyViewFilterType):
    type = "not_empty"
