from baserow.contrib.database.formula.exceptions import BaserowFormulaException


class InvalidFormulaType(BaserowFormulaException):
    pass


class UnknownFormulaType(BaserowFormulaException):
    def __init__(self, unknown_formula_type):
        super().__init__(
            f"unknown formula type found on formula field of {unknown_formula_type}"
        )
