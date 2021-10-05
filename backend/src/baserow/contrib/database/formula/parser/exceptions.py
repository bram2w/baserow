from baserow.contrib.database.formula.exceptions import BaserowFormulaException


class InvalidNumberOfArguments(BaserowFormulaException):
    def __init__(self, function_def, num_args):
        if num_args == 1:
            error_prefix = "1 argument was"
        else:
            error_prefix = f"{num_args} arguments were"
        super().__init__(
            f"{error_prefix} given to the {function_def}, it must instead "
            f"be given {function_def.num_args}"
        )


class MaximumFormulaSizeError(BaserowFormulaException):
    def __init__(self):
        super().__init__("it exceeded the maximum formula size")


class UnknownFieldByIdReference(BaserowFormulaException):
    def __init__(self, unknown_field_id):
        super().__init__(
            f"there is no field with id {unknown_field_id} but the formula"
            f" included a direct reference to it"
        )


class UnknownOperator(BaserowFormulaException):
    def __init__(self, operatorText):
        super().__init__(f"it used the unknown operator {operatorText}")


class BaserowFormulaSyntaxError(BaserowFormulaException):
    pass
