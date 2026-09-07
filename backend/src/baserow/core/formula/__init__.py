from typing import Any

from baserow.core.formula.parser.exceptions import (
    BaserowFormulaException,
    BaserowFormulaSyntaxError,
    MaximumFormulaSizeError,
)
from baserow.core.formula.parser.generated.BaserowFormula import BaserowFormula
from baserow.core.formula.parser.generated.BaserowFormulaVisitor import (
    BaserowFormulaVisitor,
)
from baserow.core.formula.text_format import strip_format
from baserow.core.formula.types import (
    BASEROW_FORMULA_MODE_RAW,
    BaserowFormulaObject,
    FormulaContext,
    FunctionCollection,
)

__all__ = [
    BaserowFormulaException,
    MaximumFormulaSizeError,
    BaserowFormulaVisitor,
    BaserowFormula,
    BaserowFormulaSyntaxError,
]

from baserow.core.formula.parser.formula_execution_visitor import (
    BaserowFormulaExecutionVisitor,
)
from baserow.core.formula.parser.parser import get_parse_tree_for_formula


def resolve_formula(
    formula: BaserowFormulaObject,
    functions: FunctionCollection,
    formula_context: FormulaContext,
) -> Any:
    """
    Helper to resolve a formula given the formula_context.

    :param formula: the formula itself.
    :param functions: The collection of functions that can be used in formulas.
    :param formula_context: A dict like object that contains the data that can
        be accessed in from the formulas.
    :return: the formula result.
    """

    # The text format marker is not part of the formula: it is never resolved
    # and never part of the result.
    bare_formula = strip_format(formula["formula"])

    # If we receive a blank formula string, don't attempt to parse it.
    if not bare_formula:
        return bare_formula

    if formula["mode"] == BASEROW_FORMULA_MODE_RAW:
        return bare_formula

    tree = get_parse_tree_for_formula(bare_formula)
    return BaserowFormulaExecutionVisitor(functions, formula_context).visit(tree)
