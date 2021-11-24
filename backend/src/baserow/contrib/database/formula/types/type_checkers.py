from baserow.contrib.database.formula.types.formula_type import (
    BaserowFormulaType,
)
from baserow.contrib.database.formula.types.formula_types import (
    BaserowFormulaNumberType,
)
from baserow.contrib.database.formula.types.type_checker import (
    SingleArgumentTypeChecker,
)


class OnlyIntegerNumberTypes(SingleArgumentTypeChecker):
    def check(self, type_to_check: BaserowFormulaType) -> bool:
        return (
            isinstance(type_to_check, BaserowFormulaNumberType)
            and type_to_check.number_decimal_places == 0
        )

    def invalid_message(self, type_which_failed_check: BaserowFormulaType) -> str:
        return "a whole number with no decimal places"
