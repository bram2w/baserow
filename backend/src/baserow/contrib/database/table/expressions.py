from django.contrib.postgres.fields import ArrayField
from django.db.models import Func, IntegerField, TextField


class BaserowTableRowCount(Func):
    function = "get_baserow_table_row_count"
    output_field = IntegerField()
    arity = 1


class BaserowTableFileUniques(Func):
    template = "(SELECT UNNEST(%(function)s(%(expressions)s)))"
    function = "get_distinct_baserow_table_file_uniques"
    output_field = ArrayField(TextField())
    arity = 1
