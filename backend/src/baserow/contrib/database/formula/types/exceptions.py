from typing import List

from baserow.contrib.database.formula.exceptions import BaserowFormulaException


class InvalidFormulaType(BaserowFormulaException):
    pass


class NoCircularReferencesError(BaserowFormulaException):
    def __init__(self, visited_fields: List[str]):
        super().__init__(
            "it references another field, which eventually references back to this "
            f"field causing an incalculable circular loop of "
            f"{'->'.join(visited_fields)}"
        )


class NoSelfReferencesError(BaserowFormulaException):
    def __init__(self):
        super().__init__(
            "it references itself which is impossible to calculate a result for"
        )


class UnknownFormulaType(BaserowFormulaException):
    def __init__(self, unknown_formula_type):
        super().__init__(
            f"unknown formula type found on formula field of {unknown_formula_type}"
        )
