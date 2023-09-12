from baserow.core.formula.parser.exceptions import BaserowFormulaException


class InvalidFormulaType(BaserowFormulaException):
    pass


class UnknownFormulaType(BaserowFormulaException):
    def __init__(self, unknown_formula_type):
        super().__init__(
            f"unknown formula type found on formula field of {unknown_formula_type}"
        )


def get_invalid_field_and_table_formula_error(
    unknown_field_name: str, table_name: str
) -> str:
    return (
        f"references the deleted or unknown field {unknown_field_name} in table "
        f"{table_name}"
    )
