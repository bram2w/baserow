import re
from typing import TYPE_CHECKING, Any, Dict, List, Type

from django.contrib.postgres.fields import JSONField
from django.db.models import BooleanField, F
from django.db.models import Field as DjangoField
from django.db.models import Q, Value
from django.db.models.expressions import RawSQL

from loguru import logger

from baserow.contrib.database.fields.field_filters import (
    AnnotatedQ,
    OptionallyAnnotatedQ,
)
from baserow.contrib.database.formula.expression_generator.django_expressions import (
    BaserowFilterExpression,
    ComparisonOperator,
    JSONArrayAllAreExpr,
    JSONArrayCompareNumericValueExpr,
    JSONArrayContainsValueLengthLowerThanExpr,
)

if TYPE_CHECKING:
    from baserow.contrib.database.fields.models import Field


class HasValueEmptyFilterSupport:
    def get_in_array_empty_value(self, field: "Field") -> Any:
        """
        Returns the value to use for filtering empty values in an array. An empty string
        is used by default and works for test-like fields, but for number fields or
        other types, this method should be overridden returning None or the most
        appropriate value.

        :param field: The related field's instance.
        :return: The value to use for filtering empty values in an array.
        """

        return ""

    def get_in_array_empty_query(
        self, field_name: str, model_field: DjangoField, field: "Field"
    ) -> OptionallyAnnotatedQ:
        """
        Specifies a Q expression to filter empty values contained in an array.

        :param field_name: The name of the field.
        :param model_field: The field's actual django field model instance.
        :param field: The related field's instance.
        :return: A Q or AnnotatedQ filter given value.
        """

        empty_value = self.get_in_array_empty_value(field)
        return Q(
            **{f"{field_name}__contains": Value([{"value": empty_value}], JSONField())}
        )


class HasValueEqualFilterSupport:
    def get_in_array_is_query(
        self, field_name: str, value: str, model_field: DjangoField, field: "Field"
    ) -> OptionallyAnnotatedQ:
        """
        Specifies a Q expression to filter exact values contained in an array.

        :param field_name: The name of the field.
        :param value: The value to check if it is contained in array.
        :param model_field: The field's actual django field model instance.
        :param field: The related field's instance.
        :return: A Q or AnnotatedQ filter given value.
        """

        return Q(**{f"{field_name}__contains": Value([{"value": value}], JSONField())})


class HasValueContainsFilterSupport:
    def get_in_array_contains_query(
        self, field_name: str, value: str, model_field: DjangoField, field: "Field"
    ) -> OptionallyAnnotatedQ:
        """
        Specifies a Q expression to filter values in an array that contain a
        specific value.

        :param field_name: The name of the field.
        :param value: The value to check if it is contained in array.
        :param model_field: The field's actual django field model instance.
        :param field: The related field's instance.
        :return: A Q or AnnotatedQ filter given value.
        """

        return get_jsonb_contains_filter_expr(model_field, value)


class HasValueContainsWordFilterSupport:
    def get_in_array_contains_word_query(
        self, field_name: str, value: str, model_field: DjangoField, field: "Field"
    ) -> OptionallyAnnotatedQ:
        """
        Specifies a Q expression to filter values in an array that contain a specific
        word.

        :param field_name: The name of the field.
        :param value: The value to check if it is contained in array.
        :param model_field: Django model field instance.
        :param field: The related Baserow field's instance containing field's metadata.
        :return: A Q or AnnotatedQ filter given value.
        """

        return get_jsonb_contains_word_filter_expr(model_field, value)


class HasValueLengthIsLowerThanFilterSupport:
    def get_in_array_length_is_lower_than_query(
        self, field_name: str, value: str, model_field: DjangoField, field: "Field"
    ) -> OptionallyAnnotatedQ:
        """
        Specifies a Q expression to filter values in an array that has lower
        than length.

        :param field_name: The name of the field.
        :param value: The value representing the length to use for the check.
        :param model_field: Django model field instance.
        :param field: The related Baserow field's instance containing field's metadata.
        :return: A Q or AnnotatedQ filter given value.
        """

        try:
            converted_value = int(value)
        except (TypeError, ValueError):
            return Q()
        annotation_query = JSONArrayContainsValueLengthLowerThanExpr(
            F(field_name), Value(converted_value), output_field=BooleanField()
        )
        hashed_value = hash(value)
        return AnnotatedQ(
            annotation={
                f"{field_name}_has_value_length_is_lower_than_{hashed_value}": annotation_query
            },
            q={f"{field_name}_has_value_length_is_lower_than_{hashed_value}": True},
        )


class HasAllValuesEqualFilterSupport:
    def get_has_all_values_equal_query(
        self, field_name: str, value: str, model_field: DjangoField, field: "Field"
    ) -> "OptionallyAnnotatedQ":
        """
         Creates a query expression to filter rows where all values of an array in
         the specified field are equal to a specific value

         :param field_name: The name of the field
         :param value: The value that should be present in all array elements
             in the field
        :param model_field: Django model field instance.
         :param field: The related Baserow field's instance containing field's metadata.
         :return: A Q or AnnotatedQ filter given value.
        """

        try:
            return get_array_json_filter_expression(
                JSONArrayAllAreExpr, field_name, Value(value)
            )

        except Exception as err:
            logger.error(
                f"Error when creating {self.type} filter expression "
                f"for {field_name} field with {value} value: {err}"
            )
            return self.default_filter_on_exception()


class HasNumericValueComparableToFilterSupport:
    def get_has_numeric_value_comparable_to_filter_query(
        self,
        field_name: str,
        value: str,
        model_field: DjangoField,
        field: "Field",
        comparison_op: ComparisonOperator,
    ) -> OptionallyAnnotatedQ:
        return get_array_json_filter_expression(
            JSONArrayCompareNumericValueExpr,
            field_name,
            Value(value),
            comparison_op=comparison_op,
        )


def get_array_json_filter_expression(
    json_expression: Type[BaserowFilterExpression],
    field_name: str,
    value: Value,
    **extra: Dict[str, Any],
) -> AnnotatedQ:
    """
    Helper function to generate an AnnotatedQ for the given field and filtering
    expression. This function ensure a consistent way to name the annotations so they
    don't clash when combined with similar filters for different fields or values.


    :param json_expression: BaserowFilterExpression to use for filtering.
    :param field_name: the name of the field
    :param value: Value expression containing the filter value with the proper type.
    :param extra: extra arguments for the json_expression.
    :return: the annotated query for the filter.
    """

    annotation_query = json_expression(
        F(field_name), value, output_field=BooleanField(), **extra
    )
    expr_name = json_expression.__name__.lower()
    hashed_value = hash(value)
    annotation_name = f"{field_name}_{expr_name}_{hashed_value}"
    return AnnotatedQ(
        annotation={annotation_name: annotation_query},
        q={annotation_name: True},
    )


def get_jsonb_contains_filter_expr(
    model_field: DjangoField, value: str, query_path: str = "$[*].value"
) -> OptionallyAnnotatedQ:
    """
    Returns an AnnotatedQ that will filter rows where the JSON field contains the
    specified value or an empty filter if the value provided is an emtpy string. The
    value is matched using a case-insensitive LIKE query. Providing a query_path allows
    for filtering on a specific path in the JSON field.

    :param model_field: The django model field to filter on. The field is used to get
        the model for the subquery and the field name.
    :param value: The value to use to create the contains filter, case-insensitive.
    :param query_path: The path in the JSON field to filter on. Defaults to
        "$[*].value".
    :return: An AnnotatedQ that will filter rows where the JSON field contains the
    """

    # If an empty value has been provided we do not want to filter at all.
    if value == "":
        return Q()

    field_name = model_field.name
    raw_sql = f"""
        EXISTS(
            SELECT 1
            FROM jsonb_path_query("{field_name}", %s) elem
            WHERE UPPER(elem::text) LIKE UPPER(%s)
        )
    """  # nosec B608 {field_name}
    expr = RawSQL(raw_sql, (query_path, f"%{value}%"))  # nosec B611
    annotation_name = f"{field_name}_contains_{hash(value)}"
    return AnnotatedQ(
        annotation={annotation_name: expr},
        q=Q(**{annotation_name: True}),
    )


def get_jsonb_contains_word_filter_expr(
    model_field: DjangoField, value: str, query_path: str = "$[*].value"
) -> OptionallyAnnotatedQ:
    """
    Returns an AnnotatedQ that will filter rows where the JSON field contains the
    specified word or an empty filter if the value provided is an emtpy string. The
    value is matched using a case-insensitive LIKE query. Providing a query_path allows
    for filtering on a specific path in the JSON field.

    :param model_field: The django model field to filter on. The field is used to get
        the model for the subquery and the field name.
    :param value: The value to use to create the contains word filter, case-insensitive.
    :param query_path: The path in the JSON field to filter on. Defaults to
        "$[*].value".
    :return: An AnnotatedQ that will filter rows where the JSON field contains the
        specified word.
    """

    # If an empty value has been provided we do not want to filter at all.
    if value == "":
        return Q()

    field_name = model_field.name
    re_value = re.escape(value.upper())
    raw_sql = f"""
        EXISTS(
            SELECT 1
            FROM jsonb_path_query("{field_name}", %s) elem
            WHERE UPPER(elem::text) ~ %s
        )
    """  # nosec B608 {field_name}
    expr = RawSQL(raw_sql, (query_path, rf"\m{re_value}\M"))  # nosec B611

    annotation_name = f"{field_name}_contains_word_{hash(value)}"
    return AnnotatedQ(
        annotation={annotation_name: expr},
        q=Q(**{annotation_name: True}),
    )


def get_jsonb_has_any_in_value_filter_expr(
    model_field: DjangoField,
    value: List[int],
    query_path: str = "$[*].id",
) -> OptionallyAnnotatedQ:
    """
    Returns an AnnotatedQ that will filter rows where the JSON field contains any of the
    IDs provided in value. Providing a query_path allows for
    filtering on a specific path in the JSON field.

    :param model_field: The django model field to filter on. The field is used to get
        the model for the subquery and the field name.
    :param value: A list of IDs to filter on. The list cannot be empty.
    :param query_path: The path in the JSON field to filter on. Defaults to "$[*].id".
    :return: An AnnotatedQ that will filter rows where the JSON field contains any of
        the select option IDs provided in the value.
    """

    sql_ids = "||".join([f"(@ == {v})" for v in value])
    field_name = model_field.name

    raw_sql = f"""
        EXISTS(
            SELECT 1
            FROM jsonb_path_exists("{field_name}", %s) elem
            WHERE elem = true
        )
    """  # nosec B608 {field_name}
    expr = RawSQL(raw_sql, (f"{query_path} ? ({sql_ids})",))  # nosec B611

    annotation_name = f"{field_name}_has_any_of_{hash(sql_ids)}"
    return AnnotatedQ(
        annotation={annotation_name: expr},
        q=Q(**{annotation_name: True}),
    )


def get_jsonb_has_exact_value_filter_expr(
    model_field: DjangoField, value: List[int]
) -> OptionallyAnnotatedQ:
    """
    Returns an AnnotatedQ that filters rows where the JSON field exactly matches the
    provided IDs. The JSON field must be an array of objects, each containing a 'value'
    key, which is an array of objects with 'id' keys. For example:
    [{"value": [{"id": 1}, {"id": 2}]}, {"value": [{"id": 3}]}, ...]

    :param model_field: The Django model field to filter on.
    :param value: A list of IDs to match. The list cannot be empty.
    :return: An AnnotatedQ that filters rows with the exact IDs in the JSON field.
    """

    field_name = model_field.name
    sql_ids = sorted(set(value))

    raw_sql = f"""
        EXISTS(
            SELECT 1
            FROM jsonb_array_elements("{field_name}") top_obj
            WHERE (
                SELECT array_agg((inner_el->>'id')::int ORDER BY (inner_el->>'id')::int)
                FROM jsonb_array_elements(top_obj->'value') inner_el
            ) = %s::int[]
        )
    """  # nosec B608 {field_name}
    expr = RawSQL(raw_sql, (sql_ids,))  # nosec B611

    annotation_name = f"{field_name}_has_any_of_{hash(tuple(sql_ids))}"
    return AnnotatedQ(
        annotation={annotation_name: expr},
        q=Q(**{annotation_name: True}),
    )
