from baserow.core.formula.runtime_formula_types import (
    RuntimeAdd,
    RuntimeConcat,
    RuntimeGet,
)
from baserow.core.registry import Registry
from baserow.formula.parser.exceptions import FormulaFunctionTypeDoesNotExist


class BaserowRuntimeFormulaFunctionRegistry(Registry):
    name = "formula_runtime_function"
    does_not_exist_exception_class = FormulaFunctionTypeDoesNotExist


formula_runtime_function_registry = BaserowRuntimeFormulaFunctionRegistry()


def register_runtime_formula_function_types():
    formula_runtime_function_registry.register(RuntimeConcat())
    formula_runtime_function_registry.register(RuntimeGet())
    formula_runtime_function_registry.register(RuntimeAdd())
