from django.db.models import Expression, DateTimeField, Value


class Timezone(Expression):
    """
    This expression can convert an existing datetime value to another timezone. It
    can for example by used like this:

    ```
    SomeModel.objects.all().annotate(
        created_on_in_amsterdam=Timezone("created_on", "Europe/Amsterdam")
    ).filter(created_on_in_amsterdam__day=1)
    ```

    It will eventually result in `created_on at time zone 'Europe/Amsterdam'`
    """

    def __init__(self, expression, timezone):
        super().__init__(output_field=DateTimeField())
        self.source_expression = self._parse_expressions(expression)[0]
        self.timezone = timezone

    def resolve_expression(
        self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False
    ):
        c = self.copy()
        c.is_summary = summarize
        c.source_expression = self.source_expression.resolve_expression(
            query, allow_joins, reuse, summarize, for_save
        )
        return c

    def __repr__(self):
        return "{}({}, {})".format(
            self.__class__.__name__,
            self.source_expression,
            self.timezone,
        )

    def as_sql(self, compiler, connection):
        params = []
        field_sql, field_params = compiler.compile(self.source_expression)
        timezone_sql, timezone_params = compiler.compile(Value(self.timezone))
        params.extend(field_params)
        params.extend(timezone_params)
        return f"{field_sql} at time zone {timezone_sql}", params
