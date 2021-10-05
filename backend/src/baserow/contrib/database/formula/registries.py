from baserow.core.registry import Registry


class BaserowFormulaFunctionRegistry(Registry):
    name = "formula_function"


formula_function_registry = BaserowFormulaFunctionRegistry()
