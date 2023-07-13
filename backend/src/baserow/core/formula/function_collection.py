from baserow.core.formula.registries import formula_runtime_function_registry
from baserow.formula.parser.python_executor import FunctionCollection


class RuntimeFunctionCollection(FunctionCollection):
    def get(self, name: str):
        return formula_runtime_function_registry.get(name)
