from django.conf import settings

from baserow.contrib.database.formula.exceptions import BaserowFormulaException


class InvalidStringLiteralProvided(BaserowFormulaException):
    pass


class InvalidIntLiteralProvided(BaserowFormulaException):
    pass


class InvalidDecimalLiteralProvided(BaserowFormulaException):
    pass


class UnknownFieldReference(BaserowFormulaException):
    def __init__(self, unknown_field_name):
        super().__init__(
            f"there is no field called {unknown_field_name} but the "
            f"formula contained a reference to it"
        )


class TooLargeStringLiteralProvided(BaserowFormulaException):
    def __init__(self):
        super().__init__(
            f"an embedded string in the formula over the "
            f"maximum length of {settings.MAX_FORMULA_STRING_LENGTH} "
        )
