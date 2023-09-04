from baserow.core.formula.parser.exceptions import FormulaFunctionTypeDoesNotExist
from baserow.core.registry import Registry


class BaserowFormulaFunctionRegistry(Registry):
    name = "formula_function"
    does_not_exist_exception_class = FormulaFunctionTypeDoesNotExist


formula_function_registry = BaserowFormulaFunctionRegistry()
