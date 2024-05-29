from typing import Callable, List, Optional, Union

from django.db.models import (
    CharField,
    Expression,
    F,
    Func,
    OuterRef,
    QuerySet,
    Subquery,
    TextField,
    Value,
)
from django.db.models.expressions import Combinable
from django.db.models.functions import Cast

import typing_extensions

if typing_extensions.TYPE_CHECKING:
    from baserow.contrib.database.fields.models import Field


def extract_jsonb_list_values_to_array(
    queryset: QuerySet,
    array_elements_expr: Union[Combinable, Expression],
    path_to_value_in_jsonb_list: Optional[List[Expression]] = None,
    transform_value_to_text_func: Optional[Callable[[Expression], Expression]] = None,
    extract_as_text: bool = True,
) -> Expression:
    """
    For a field whose cells contain a JSONB list of objects (File and Lookup fields)
    this function can construct a Django expression to obtain a ARRAY (which can then
    be used or aggregated with more Funcs) accessing a JSON path into each object.

    For example a table with a JSONB field with cell values like:
    Row 1) - [{value: {value: 'a'}}, {value: {value: 'b'}]
    Row 2) - [{value: {value: 'c'}}, {value: {value: 'd'}]
    You can then say select the concatenated inner values per row like so:

    ```
    results = model.objects.values_list(
                result=Func(
                        extract_jsonb_list_values_to_array(
                            field,
                            model.objects,
                            [Value('value'), Value('value')],
                        )
                        Value(','),
                        function='array_to_string'
                    )
                )
    assert results[0] == 'a,b'
    assert results[1] == 'b,c'
    ```

    :param array_elements_expr: An Expression or a Combinable (e.g. F("field_name"))
        that contains the JSONB you wish to query
    :param queryset: A queryset over the model containing the field
    :param path_to_value_in_jsonb_list: An optional list of arguments to pass to the
        jsonb_extract_path_text function to describe the path in the JSONB object
        to describe. Defaults to just 'value'.
    :param transform_value_to_text_func: An optional callable which will be given
        an inner expression that returns the extracted jsonb value in each object,
        which can then transform it to another value before it is aggregated into
        an array.
    :param extract_as_text: When true the jsonb value will be extracted as a text value
        , when false instead the raw jsonb will be provided to the transform func.

    :return: A Django expression.
    """

    if not path_to_value_in_jsonb_list:
        path_to_value_in_jsonb_list = [Value("value", output_field=CharField())]
    if not transform_value_to_text_func:

        def transform_value_to_text_func(x):
            return Cast(x, output_field=CharField())

    return Func(
        Subquery(
            queryset.filter(pk=OuterRef("pk"))
            .order_by()
            .values("pk")
            .annotate(
                transformed_values=transform_value_to_text_func(
                    json_extract_path(
                        Func(array_elements_expr, function="jsonb_array_elements"),
                        path_to_value_in_jsonb_list,
                        extract_as_text,
                    )
                ),
            )
            .values("transformed_values")
        ),
        function="array",
    )


def json_extract_path(expr, path_to_value_in_jsonb_list, extract_as_text=True):
    return Func(
        expr,
        *path_to_value_in_jsonb_list,
        function="jsonb_extract_path_text" if extract_as_text else "jsonb_extract_path",
        output_field=TextField(),
    )


def extract_jsonb_array_values_to_single_string(
    field: "Field",
    queryset: QuerySet,
    path_to_value_in_jsonb_list: Optional[List[Expression]] = None,
    transform_value_to_text_func: Optional[Callable[[Expression], Expression]] = None,
    extract_as_text: bool = True,
    delimiter: str = " ",
):
    """
    For a field whose cells contain a JSONB list of objects (File and Lookup fields)
    this function can construct a Django expression to obtain a string accessing a
    JSON path into each object.

    For example a table with a JSONB field with cell values like:
    Row 1) - [{value: {value: 'a'}}, {value: {value: 'b'}]
    Row 2) - [{value: {value: 'c'}}, {value: {value: 'd'}]
    You can then say select the concatted inner values per row like so:

    ```
    results = model.objects.values_list(
                result=extract_jsonb_array_values_to_single_string(
                            field,
                            model.objects,
                            [Value('value'), Value('value')],
                        )
                )
    assert results[0] == 'a,b'
    assert results[1] == 'b,c'
    ```

    :param field: The field whose column that contains the JSONB you wish to query
    :param queryset: A queryset over the model containing the field
    :param path_to_value_in_jsonb_list: An optional list of arguments to pass to the
        jsonb_extract_path_text function to describe the path in the JSONB object
        to describe. Defaults to just 'value'.
    :param transform_value_to_text_func: An optional callable which will be given
        an inner expression that returns the extracted jsonb value in each object,
        which can then transform it to another value before it is aggregated into
        an array.
    :param extract_as_text: When true the jsonb value will be extracted as a text value
        , when false instead the raw jsob will be provided to the transform func.
    :param delimiter: The delimiter used when concatting the array values into a string.

    :return: A Django expression.
    """

    return Func(
        extract_jsonb_list_values_to_array(
            queryset,
            F(field.db_column),
            path_to_value_in_jsonb_list,
            transform_value_to_text_func,
            extract_as_text,
        ),
        Value(delimiter),
        function="array_to_string",
        output_field=TextField(),
    )
