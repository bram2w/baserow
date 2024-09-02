import typing

from django.db import connection

from baserow.contrib.database.formula.types.visitors import FormulaTypingVisitor
from baserow.core.formula.parser.exceptions import MaximumFormulaSizeError

if typing.TYPE_CHECKING:
    from baserow.contrib.database.fields.models import FormulaField


def calculate_typed_expression(formula_field, field_cache):
    """
    Core algorithm used to generate the internal typed expression for a given user
    supplied formula. The resulting typed expression can be directly translated to a
    Django expression for use.

    :param formula_field: The formula field to calculate the typed internal expression
        for.
    :param field_cache: A field lookup cache that will be used to lookup fields
        referenced by this field.
    :return: A typed internal expression.
    """

    try:
        untyped_expression = formula_field.cached_untyped_expression

        typed_expression = untyped_expression.accept(
            FormulaTypingVisitor(formula_field, field_cache)
        )
        expression_type = typed_expression.expression_type
        merged_expression_type = (
            expression_type.new_type_with_user_and_calculated_options_merged(
                formula_field
            )
        )
        # Take into account any user set formatting options on this formula field.
        typed_expr_merged_with_user_options = typed_expression.with_type(
            merged_expression_type
        )
        if typed_expr_merged_with_user_options.many:
            de_many_expr = (
                typed_expr_merged_with_user_options.expression_type.collapse_many(
                    typed_expr_merged_with_user_options
                )
            )
        else:
            de_many_expr = typed_expr_merged_with_user_options

        wrapped_expr = de_many_expr.expression_type.wrap_at_field_level(de_many_expr)

        return wrapped_expr
    except RecursionError:
        raise MaximumFormulaSizeError()


def _check_if_formula_type_change_requires_drop_recreate(old_formula_field, new_type):
    old_type = old_formula_field.cached_formula_type

    return new_type.should_recreate_when_old_type_was(old_type)


def recreate_formula_field_if_needed(
    field: "FormulaField",
    old_field: "FormulaField",
    force_recreate_column: bool = False,
):
    if force_recreate_column or _check_if_formula_type_change_requires_drop_recreate(
        old_field, field.cached_formula_type
    ):
        model = field.table.get_model(
            fields=[field], field_ids=[], add_dependencies=False
        )
        from baserow.contrib.database.fields.registries import field_converter_registry

        field_converter_registry.get("formula").alter_field(
            old_field,
            field,
            model,
            model,
            model._meta.get_field(old_field.db_column),
            model._meta.get_field(field.db_column),
            None,
            connection,
            force_recreate_column=force_recreate_column,
        )
