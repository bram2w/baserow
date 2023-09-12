import pytest

from baserow.core.formula.parser.exceptions import (
    BaserowFormulaSyntaxError,
    InvalidNumberOfArguments,
)
from baserow.core.formula.parser.parser import get_parse_tree_for_formula
from baserow.core.formula.parser.python_executor import BaserowPythonExecutor
from baserow.core.formula.registries import formula_runtime_function_registry
from baserow.test_utils.helpers import load_test_cases

TEST_DATA = load_test_cases("formula_runtime_cases")

VALID_FORMULA_TESTS = TEST_DATA["VALID_FORMULA_TESTS"]
INVALID_FORMULA_TESTS = TEST_DATA["INVALID_FORMULA_TESTS"]


@pytest.mark.parametrize("test_data", VALID_FORMULA_TESTS)
def test_valid_formulas(test_data):
    formula = test_data["formula"]
    result = test_data["result"]
    context = test_data["context"]

    tree = get_parse_tree_for_formula(formula)
    assert (
        BaserowPythonExecutor(formula_runtime_function_registry, context).visit(tree)
        == result
    )


@pytest.mark.parametrize("test_data", INVALID_FORMULA_TESTS)
def test_invalid_formulas(test_data):
    formula = test_data["formula"]
    context = test_data["context"]

    with pytest.raises(Exception):
        tree = get_parse_tree_for_formula(formula)
        BaserowPythonExecutor(formula_runtime_function_registry, context).visit(tree)


def test_formula_function_does_not_exist():
    with pytest.raises(BaserowFormulaSyntaxError):
        tree = get_parse_tree_for_formula("notExistingFunction(1,2,3)")
        BaserowPythonExecutor(formula_runtime_function_registry, {}).visit(tree)


def test_invalid_number_of_arguments():
    with pytest.raises(InvalidNumberOfArguments):
        tree = get_parse_tree_for_formula("get(1,2)")
        BaserowPythonExecutor(formula_runtime_function_registry, {}).visit(tree)
