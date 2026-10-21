from baserow.core.formula import (
    BaserowFormula,
    BaserowFormulaException,
    BaserowFormulaVisitor,
    get_parse_tree_for_formula,
)
from baserow.core.formula.types import BASEROW_FORMULA_MODE_RAW
from baserow.core.utils import to_path

from .runtime import unwrap_expression


class DashboardFilterReferenceVisitor(BaserowFormulaVisitor):
    def __init__(self):
        self.filter_ids = set()

    def visitFunctionCall(self, ctx):
        arguments = ctx.expr()
        if ctx.func_name().getText().lower() == "get" and len(arguments) == 1:
            argument = unwrap_expression(arguments[0])
            if isinstance(argument, BaserowFormula.StringLiteralContext):
                path = to_path(argument.getText()[1:-1])
                if (
                    len(path) >= 2
                    and path[0] == "dashboard_filter"
                    and path[1].isdigit()
                ):
                    self.filter_ids.add(int(path[1]))
        return self.visitChildren(ctx)


def get_referenced_dashboard_filters(formula):
    """Find control references, including those inside calculated conditions."""

    if formula["mode"] == BASEROW_FORMULA_MODE_RAW or not formula["formula"]:
        return set()
    visitor = DashboardFilterReferenceVisitor()
    try:
        visitor.visit(get_parse_tree_for_formula(formula["formula"]))
    except (BaserowFormulaException, RecursionError):
        # Unrelated invalid formulas must not prevent deleting a control.
        return set()
    return visitor.filter_ids
