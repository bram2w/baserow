from baserow.core.registry import Registry

from .exceptions import FormulaFunctionTypeDoesNotExist


class BaserowFormulaFunctionRegistry(Registry):
    name = "formula_function"
    does_not_exist_exception_class = FormulaFunctionTypeDoesNotExist


formula_function_registry = BaserowFormulaFunctionRegistry()
