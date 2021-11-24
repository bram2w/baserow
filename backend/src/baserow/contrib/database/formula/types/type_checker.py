import abc
from typing import List, Type, Union, Callable

from baserow.contrib.database.formula.types.formula_type import (
    BaserowFormulaType,
    BaserowFormulaValidType,
)


class SingleArgumentTypeChecker(abc.ABC):
    @abc.abstractmethod
    def check(self, type_to_check: BaserowFormulaType) -> bool:
        pass

    @abc.abstractmethod
    def invalid_message(self, type_which_failed_check: BaserowFormulaType) -> str:
        pass


BaserowListOfValidTypes = List[Type[BaserowFormulaValidType]]
BaserowSingleArgumentTypeChecker = Union[
    BaserowListOfValidTypes, SingleArgumentTypeChecker
]
"""
Defines a way of checking a single provided argument has a valid type or not.
"""

BaserowArgumentTypeChecker = Union[
    Callable[[int, List[BaserowFormulaType]], BaserowListOfValidTypes],
    List[BaserowSingleArgumentTypeChecker],
]
"""
Defines a way of checking if all the arguments for a function.
Either a callable which is given the argument index to check and the list of argument
types and should return a list of valid types for that argument. Or instead can just be
a list of single arg type checkers where the Nth position in the list is the type
checker for the Nth argument.
"""
