from typing import Dict, Optional

from baserow.contrib.database.formula.parser.exceptions import (
    MaximumFormulaSizeError,
)
from baserow.contrib.database.formula.parser.generated.BaserowFormula import (
    BaserowFormula,
)
from baserow.contrib.database.formula.parser.generated.BaserowFormulaVisitor import (
    BaserowFormulaVisitor,
)
from baserow.contrib.database.formula.parser.parser import (
    convert_string_literal_token_to_string,
    convert_string_to_string_literal_token,
    get_parse_tree_for_formula,
)


# noinspection DuplicatedCode
class UpdateFieldNameFormulaVisitor(BaserowFormulaVisitor):
    """
    Visits nodes of the BaserowFormula antlr parse tree returning the formula in string
    form, but with field(name) and field_by_id(id) references replaced according to the
    input dictionaries.
    """

    def __init__(
        self,
        field_names_to_update: Optional[Dict[str, str]] = None,
        field_ids_to_replace_with_name_refs: Optional[Dict[int, str]] = None,
        field_names_to_replace_with_id_refs: Optional[Dict[str, int]] = None,
    ):
        if field_names_to_update is None:
            field_names_to_update = {}
        if field_ids_to_replace_with_name_refs is None:
            field_ids_to_replace_with_name_refs = {}
        if field_names_to_replace_with_id_refs is None:
            field_names_to_replace_with_id_refs = {}

        self.field_names_to_replace_with_id_refs = field_names_to_replace_with_id_refs
        self.field_names_to_update = field_names_to_update
        self.field_ids_to_replace_with_name_refs = field_ids_to_replace_with_name_refs

    def visitRoot(self, ctx: BaserowFormula.RootContext):
        return ctx.expr().accept(self)

    def visitStringLiteral(self, ctx: BaserowFormula.StringLiteralContext):
        return ctx.getText()

    def visitDecimalLiteral(self, ctx: BaserowFormula.DecimalLiteralContext):
        return ctx.getText()

    def visitBooleanLiteral(self, ctx: BaserowFormula.BooleanLiteralContext):
        return ctx.getText()

    def visitBrackets(self, ctx: BaserowFormula.BracketsContext):
        return ctx.expr().accept(self)

    def visitFunctionCall(self, ctx: BaserowFormula.FunctionCallContext):
        function_name = ctx.func_name().getText()
        args = [expr.accept(self) for expr in (ctx.expr())]
        args_with_any_field_names_replaced = ",".join(args)
        return f"{function_name}({args_with_any_field_names_replaced})"

    def visitBinaryOp(self, ctx: BaserowFormula.BinaryOpContext):
        args = [expr.accept(self) for expr in (ctx.expr())]
        return args[0] + ctx.op.text + args[1]

    def visitFunc_name(self, ctx: BaserowFormula.Func_nameContext):
        return ctx.getText()

    def visitIdentifier(self, ctx: BaserowFormula.IdentifierContext):
        return ctx.getText()

    def visitIntegerLiteral(self, ctx: BaserowFormula.IntegerLiteralContext):
        return ctx.getText()

    def visitFieldReference(self, ctx: BaserowFormula.FieldReferenceContext):
        reference = ctx.field_reference()
        is_single_quote_ref = reference.SINGLEQ_STRING_LITERAL()
        field_name = convert_string_literal_token_to_string(
            reference.getText(), is_single_quote_ref
        )
        if field_name in self.field_names_to_update:
            new_name = self.field_names_to_update[field_name]
            escaped_new_name = convert_string_to_string_literal_token(
                new_name, is_single_quote_ref
            )
            field = ctx.FIELD().getText()
            return f"{field}({escaped_new_name})"
        elif field_name in self.field_names_to_replace_with_id_refs:
            return (
                f"field_by_id({self.field_names_to_replace_with_id_refs[field_name]})"
            )
        else:
            return ctx.getText()

    def visitFieldByIdReference(self, ctx: BaserowFormula.FieldByIdReferenceContext):
        field_id = int(str(ctx.INTEGER_LITERAL()))
        if field_id not in self.field_ids_to_replace_with_name_refs:
            return f"field('unknown field {field_id}')"
        new_name = self.field_ids_to_replace_with_name_refs[field_id]
        escaped_new_name = convert_string_to_string_literal_token(new_name, True)
        return f"field({escaped_new_name})"

    def visitLeftWhitespaceOrComments(
        self, ctx: BaserowFormula.LeftWhitespaceOrCommentsContext
    ):
        updated_expr = ctx.expr().accept(self)
        return ctx.ws_or_comment().getText() + updated_expr

    def visitRightWhitespaceOrComments(
        self, ctx: BaserowFormula.RightWhitespaceOrCommentsContext
    ):
        updated_expr = ctx.expr().accept(self)
        return updated_expr + ctx.ws_or_comment().getText()


def update_field_names(
    formula: str,
    field_names_to_update: Optional[Dict[str, str]] = None,
    field_ids_to_replace_with_name_refs: Optional[Dict[int, str]] = None,
    field_names_to_replace_with_id_refs: Optional[Dict[str, int]] = None,
) -> str:
    """
    :param formula: The raw formula string to update field names in.
    :param field_names_to_update: A dictionary where the keys are the old
        field names with the values being the new names to replace the old with.
    :param field_ids_to_replace_with_name_refs: To replace field_by_id references
        with specific field names then provide this dictionary of field id to name
        which will swap field_by_id(key) for a field(value). If a field id is not found
        in this dict it will be swapped for field('unknown field {id}').
    :param field_names_to_replace_with_id_refs: To replace field references
        with specific field ids then provide this dictionary of field name to id
        which will swap field(key) for a field_by_id(value). If a field name is not
        found in this dict it will be left alone.
    :return: An updated formula string where field and field_by_id references have
        been updated accordingly. Whitespace and comments will not have been modified.
    """

    try:
        tree = get_parse_tree_for_formula(formula)
        return UpdateFieldNameFormulaVisitor(
            field_names_to_update,
            field_ids_to_replace_with_name_refs,
            field_names_to_replace_with_id_refs,
        ).visit(tree)
    except RecursionError:
        raise MaximumFormulaSizeError()
