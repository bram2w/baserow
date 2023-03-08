from django.contrib.postgres.aggregates.mixins import OrderableAggMixin
from django.db.models import Aggregate, Expression, F, Field, Transform, Value


# noinspection PyAbstractClass
class BinaryOpExpr(Transform):
    template = "(%(expressions)s)"
    arity = 2


class IsNullExpr(Transform):
    template = "(%(expressions)s) IS NULL"
    arity = 1


# Django provides no way of doing a SQL equals expression with an arbitrary Django
# expression on both the LHS and RHS. Instead we have to define our own simple transform
# which joins two expressions together with a single =.
# noinspection PyAbstractClass
class EqualsExpr(BinaryOpExpr):
    arg_joiner = "="


# noinspection PyAbstractClass
class NotEqualsExpr(BinaryOpExpr):
    arg_joiner = "!="


# noinspection PyAbstractClass
class GreaterThanExpr(BinaryOpExpr):
    arg_joiner = ">"


# noinspection PyAbstractClass
class GreaterThanOrEqualExpr(BinaryOpExpr):
    arg_joiner = ">="


# noinspection PyAbstractClass
class LessThanExpr(BinaryOpExpr):
    arg_joiner = "<"


# noinspection PyAbstractClass
class LessThanEqualOrExpr(BinaryOpExpr):
    arg_joiner = "<="


# noinspection PyAbstractClass
class AndExpr(BinaryOpExpr):
    arg_joiner = " AND "


# noinspection PyAbstractClass
class OrExpr(BinaryOpExpr):
    arg_joiner = " OR "


# noinspection PyAbstractClass
class NotExpr(Transform):
    template = "(not %(expressions)s)"
    arity = 1


class TimezoneExpr(BinaryOpExpr):
    arg_joiner = " at time zone "


class BaserowStringAgg(OrderableAggMixin, Aggregate):
    function = "STRING_AGG"
    template = "%(function)s(%(distinct)s%(expressions)s %(ordering)s)"
    allow_distinct = True

    def __init__(self, expression, delimiter, **extra):
        super().__init__(expression, delimiter, **extra)

    def convert_value(self, value, expression, connection):
        if not value:
            return ""
        return value


class FileNameContainsExpr(Expression):
    # fmt: off
    template = (  # nosec b608
        f"""
        EXISTS(
            SELECT attached_files ->> 'visible_name'
            FROM JSONB_ARRAY_ELEMENTS(%(field_name)s) as attached_files
            WHERE UPPER(attached_files ->> 'visible_name') LIKE UPPER(%(value)s)
        )
        """
    )
    # fmt: on

    def __init__(self, field_name: F, value: Value, output_field: Field):
        super().__init__(output_field=output_field)
        self.field_name = field_name
        self.value = value

    def resolve_expression(
        self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False
    ):
        c = self.copy()
        c.is_summary = summarize

        c.field_name = self.field_name.resolve_expression(
            query, allow_joins, reuse, summarize, for_save
        )

        c.value = self.value.resolve_expression(
            query, allow_joins, reuse, summarize, for_save
        )

        return c

    def as_sql(self, compiler, connection, template=None):
        sql_value, params_value = compiler.compile(self.value)

        template = template or self.template
        data = {
            "field_name": f'"{self.field_name.field.column}"',
            "value": sql_value,
        }
        return template % data, params_value
