from typing import Any

from baserow.formula.parser.exceptions import (
    BaserowFormulaException,
    BaserowFormulaSyntaxError,
    MaximumFormulaSizeError,
)
from baserow.formula.parser.generated.BaserowFormula import BaserowFormula
from baserow.formula.parser.generated.BaserowFormulaVisitor import BaserowFormulaVisitor
from baserow.formula.types import FormulaContext, FunctionCollection

__all__ = [
    BaserowFormulaException,
    MaximumFormulaSizeError,
    BaserowFormulaVisitor,
    BaserowFormula,
    BaserowFormulaSyntaxError,
]


from baserow.formula.parser.parser import get_parse_tree_for_formula
from baserow.formula.parser.python_executor import BaserowPythonExecutor


def resolve_formula(
    formula: str, functions: FunctionCollection, formula_context: FormulaContext
) -> Any:
    """
    Helper to resolve a formula given the formula_context.

    :param formula: the formula itself.
    :param formula_context: A dict like object that contains the data that can
        be accessed in from the formulas.
    :return: the formula result.
    """

    tree = get_parse_tree_for_formula(formula)
    return BaserowPythonExecutor(functions, formula_context).visit(tree)
