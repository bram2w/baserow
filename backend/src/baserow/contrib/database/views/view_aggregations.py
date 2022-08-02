from django.db.models import Avg, Count, Max, Min, StdDev, Sum, Variance

from baserow.contrib.database.db.aggregations import Percentile
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

from .registries import ViewAggregationType

# See official django documentation for list of aggregator:
# https://docs.djangoproject.com/en/4.0/ref/models/querysets/#aggregation-functions


class EmptyCountViewAggregationType(ViewAggregationType):
    """
    The empty count aggregation counts how many values are considered empty for
    the given field.
    """

    type = "empty_count"

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
        PhoneNumberFieldType.type,
        SingleSelectFieldType.type,
        MultipleSelectFieldType.type,
        FormulaFieldType.compatible_with_formula_types(
            BaserowFormulaTextType.type,
            BaserowFormulaCharType.type,
            BaserowFormulaNumberType.type,
            BaserowFormulaDateType.type,
            BaserowFormulaBooleanType.type,
        ),
    ]

    def get_aggregation(self, field_name, model_field, field):
        field_type = field_type_registry.get_by_model(field)
        return Count(
            "id",
            distinct=True,
            filter=field_type.empty_query(field_name, model_field, field),
        )


class NotEmptyCountViewAggregationType(EmptyCountViewAggregationType):
    """
    The empty count aggregation counts how many values aren't considered empty for
    the given field.
    """

    type = "not_empty_count"

    def get_aggregation(self, field_name, model_field, field):
        field_type = field_type_registry.get_by_model(field)

        return Count(
            "id",
            distinct=True,
            filter=~field_type.empty_query(field_name, model_field, field),
        )


class UniqueCountViewAggregationType(ViewAggregationType):
    """
    The aggregation compute the count of distinct value for the given field.
    """

    type = "unique_count"

    compatible_field_types = [
        TextFieldType.type,
        LongTextFieldType.type,
        URLFieldType.type,
        NumberFieldType.type,
        RatingFieldType.type,
        DateFieldType.type,
        LastModifiedFieldType.type,
        CreatedOnFieldType.type,
        EmailFieldType.type,
        PhoneNumberFieldType.type,
        SingleSelectFieldType.type,
        FormulaFieldType.compatible_with_formula_types(
            BaserowFormulaTextType.type,
            BaserowFormulaCharType.type,
            BaserowFormulaNumberType.type,
            BaserowFormulaDateType.type,
        ),
    ]

    def get_aggregation(self, field_name, model_field, field):
        return Count(
            field_name,
            distinct=True,
        )


class MinViewAggregationType(ViewAggregationType):
    """
    Compute the minimum value for the given field.
    """

    type = "min"

    compatible_field_types = [
        DateFieldType.type,
        NumberFieldType.type,
        RatingFieldType.type,
        DateFieldType.type,
        LastModifiedFieldType.type,
        CreatedOnFieldType.type,
        FormulaFieldType.compatible_with_formula_types(
            BaserowFormulaNumberType.type,
            BaserowFormulaDateType.type,
        ),
    ]

    def get_aggregation(self, field_name, model_field, field):
        return Min(field_name)


class MaxViewAggregationType(ViewAggregationType):
    """
    Compute the maximum value for the given field.
    """

    type = "max"

    compatible_field_types = [
        DateFieldType.type,
        NumberFieldType.type,
        RatingFieldType.type,
        DateFieldType.type,
        LastModifiedFieldType.type,
        CreatedOnFieldType.type,
        FormulaFieldType.compatible_with_formula_types(
            BaserowFormulaNumberType.type,
            BaserowFormulaDateType.type,
        ),
    ]

    def get_aggregation(self, field_name, model_field, field):
        return Max(field_name)


class SumViewAggregationType(ViewAggregationType):
    """
    Compute the sum of all the values of the given field.
    """

    type = "sum"

    compatible_field_types = [
        NumberFieldType.type,
        RatingFieldType.type,
        FormulaFieldType.compatible_with_formula_types(
            BaserowFormulaNumberType.type,
        ),
    ]

    def get_aggregation(self, field_name, model_field, field):
        return Sum(field_name)


class AverageViewAggregationType(ViewAggregationType):
    """
    Compute the average of all the values of the given field.
    """

    type = "average"

    compatible_field_types = [
        NumberFieldType.type,
        RatingFieldType.type,
        FormulaFieldType.compatible_with_formula_types(
            BaserowFormulaNumberType.type,
        ),
    ]

    def get_aggregation(self, field_name, model_field, field):
        field_type = field_type_registry.get_by_model(field)

        return Avg(
            field_name,
            filter=~field_type.empty_query(field_name, model_field, field),
        )


class StdDevViewAggregationType(ViewAggregationType):
    """
    Compute the standard deviation of the values of the given field.
    """

    type = "std_dev"

    compatible_field_types = [
        NumberFieldType.type,
        RatingFieldType.type,
        FormulaFieldType.compatible_with_formula_types(
            BaserowFormulaNumberType.type,
        ),
    ]

    def get_aggregation(self, field_name, model_field, field):
        return StdDev(field_name)


class VarianceViewAggregationType(ViewAggregationType):
    """
    Compute the variance of the values of the given field.
    """

    type = "variance"

    compatible_field_types = [
        NumberFieldType.type,
        RatingFieldType.type,
        FormulaFieldType.compatible_with_formula_types(
            BaserowFormulaNumberType.type,
        ),
    ]

    def get_aggregation(self, field_name, model_field, field):
        return Variance(field_name)


class MedianViewAggregationType(ViewAggregationType):
    """
    Compute the median of the values of the given field.
    """

    type = "median"

    compatible_field_types = [
        NumberFieldType.type,
        RatingFieldType.type,
        FormulaFieldType.compatible_with_formula_types(
            BaserowFormulaNumberType.type,
        ),
    ]

    def get_aggregation(self, field_name, model_field, field):
        return Percentile(field_name, 0.5)


class DecileViewAggregationType(ViewAggregationType):
    """
    Compute deciles of the values of the given field.
    """

    type = "decile"

    compatible_field_types = [
        NumberFieldType.type,
        RatingFieldType.type,
        FormulaFieldType.compatible_with_formula_types(
            BaserowFormulaNumberType.type,
        ),
    ]

    def get_aggregation(self, field_name, model_field, field):
        return Percentile(field_name, [x / 10 for x in range(1, 10)])


class RangeViewAggregationType(ViewAggregationType):
    """
    Compute the min and max of the values of the given field.
    """

    type = "range"

    compatible_field_types = [
        DateFieldType.type,
        NumberFieldType.type,
        RatingFieldType.type,
        DateFieldType.type,
        LastModifiedFieldType.type,
        CreatedOnFieldType.type,
        FormulaFieldType.compatible_with_formula_types(
            BaserowFormulaNumberType.type,
            BaserowFormulaDateType.type,
        ),
    ]

    def get_aggregation(self, field_name, model_field, field):
        return {"min": Min(field_name), "max": Max(field_name)}
