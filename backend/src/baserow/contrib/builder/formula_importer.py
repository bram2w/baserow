from typing import Dict

from baserow.contrib.builder.data_providers.registries import (
    builder_data_provider_type_registry,
)
from baserow.core.formula import BaserowFormula, BaserowFormulaVisitor
from baserow.core.formula.parser.exceptions import FieldByIdReferencesAreDeprecated
from baserow.core.formula.parser.parser import get_parse_tree_for_formula
from baserow.core.utils import to_path


class BaserowFormulaImporter(BaserowFormulaVisitor):
    """
    This visitor do nothing with most of the context but update the path of the
    `get()` function.
    """

    def __init__(self, id_mapping, **kwargs):
        self.id_mapping = id_mapping
        self.extra_context = kwargs

    def visitRoot(self, ctx: BaserowFormula.RootContext):
        return ctx.expr().accept(self)

    def visitStringLiteral(self, ctx: BaserowFormula.StringLiteralContext):
        # noinspection PyTypeChecker
        return ctx.getText()

    def visitDecimalLiteral(self, ctx: BaserowFormula.DecimalLiteralContext):
        return ctx.getText()

    def visitBooleanLiteral(self, ctx: BaserowFormula.BooleanLiteralContext):
        return ctx.getText()

    def visitBrackets(self, ctx: BaserowFormula.BracketsContext):
        return ctx.expr().accept(self)

    def process_string(self, ctx):
        ctx.getText()

    def visitFunctionCall(self, ctx: BaserowFormula.FunctionCallContext):
        function_name = ctx.func_name().accept(self).lower()
        function_argument_expressions = ctx.expr()

        return self._do_func_import(function_argument_expressions, function_name)

    def _do_func_import(self, function_argument_expressions, function_name: str):
        args = [expr.accept(self) for expr in function_argument_expressions]

        # If it's a get function then let's update the path
        if function_name == "get" and isinstance(
            function_argument_expressions[0], BaserowFormula.StringLiteralContext
        ):
            unquoted_arg = args[0]

            data_provider_name, *path = to_path(unquoted_arg[1:-1])
            data_provider_type = builder_data_provider_type_registry.get(
                data_provider_name
            )
            unquoted_arg_list = data_provider_type.import_path(
                path, self.id_mapping, **self.extra_context
            )

            args = [f"'{'.'.join([data_provider_name, *unquoted_arg_list])}'"]

        return f"{function_name}({','.join(args)})"

    def visitBinaryOp(self, ctx: BaserowFormula.BinaryOpContext):
        return ctx.getText()

    def visitFunc_name(self, ctx: BaserowFormula.Func_nameContext):
        return ctx.getText()

    def visitIdentifier(self, ctx: BaserowFormula.IdentifierContext):
        return ctx.getText()

    def visitIntegerLiteral(self, ctx: BaserowFormula.IntegerLiteralContext):
        return ctx.getText()

    def visitFieldByIdReference(self, ctx: BaserowFormula.FieldByIdReferenceContext):
        raise FieldByIdReferencesAreDeprecated()

    def visitLeftWhitespaceOrComments(
        self, ctx: BaserowFormula.LeftWhitespaceOrCommentsContext
    ):
        return ctx.expr().accept(self)

    def visitRightWhitespaceOrComments(
        self, ctx: BaserowFormula.RightWhitespaceOrCommentsContext
    ):
        return ctx.expr().accept(self)


def import_formula(formula: str, id_mapping: Dict[str, str], **kwargs) -> str:
    """
    When a formula is used somewhere in the AB, it must be migrated when we import
    it because it could contains Id referencing other objects. For example, the formula
    `get('data_source.2.field_25)` references the data source with Id `2`
    and the field with Id `25`.
    In order to update the Id a special process must be applied:

    ```
    from baserow.contrib.builder.formula_importer import import_formula
    ...

    # Later in your code
    serialized_values["property_with_formula"] = import_formula(
                    serialized_values["property_with_formula"], id_mapping
                )
    ```

    :param formula: The formula to import.
    :param id_mapping: The Id map between old and new instances used during import.
    :param kwargs: Sometimes more parameters are needed by the import formula process.
      Extra kwargs are then passed to the underlying migration process.
    :return: The updated path.
    """

    if not formula:
        return formula

    tree = get_parse_tree_for_formula(formula)
    return BaserowFormulaImporter(id_mapping, **kwargs).visit(tree)
