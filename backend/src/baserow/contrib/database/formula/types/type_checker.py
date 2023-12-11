import abc
import typing
from typing import Callable, List, Type, Union

from baserow.contrib.database.formula.types.formula_type import (
    BaserowFormulaType,
    BaserowFormulaValidType,
)

if typing.TYPE_CHECKING:
    from baserow.contrib.database.formula import BaserowExpression


class SingleArgumentTypeChecker(abc.ABC):
    @abc.abstractmethod
    def check(
        self,
        arg_index: int,
        typed_expression_to_check: "BaserowExpression[BaserowFormulaType]",
    ) -> bool:
        pass

    @abc.abstractmethod
    def invalid_message(
        self,
        arg_index: int,
        type_which_failed_check: "BaserowExpression[BaserowFormulaType]",
    ) -> str:
        pass


class MustBeManyExprChecker(SingleArgumentTypeChecker):
    """
    Checks that the argument is one of the provided formula_types and it is also a
    many expression. That is it the result of a lookup or reference of a link row field
    and so represents a list of values. Expressions which are many can be safely used
    by aggregate functions.
    """

    def __init__(self, *formula_types: Type[BaserowFormulaType]):
        self.formula_types = tuple(formula_types)

    def check(
        self,
        arg_index: int,
        typed_expression_to_check: "BaserowExpression[BaserowFormulaType]",
    ) -> bool:
        return (
            self._expr_is_valid_type(typed_expression_to_check)
            and typed_expression_to_check.many
        )

    def _expr_is_valid_type(self, typed_expression_to_check):
        return isinstance(typed_expression_to_check.expression_type, self.formula_types)

    def invalid_message(
        self,
        arg_index: int,
        typed_expression_to_check: "BaserowExpression[BaserowFormulaType]",
    ) -> str:
        valid_types_str = ", or ".join(
            [str(t.type) for t in self.formula_types if t != BaserowFormulaValidType]
        )
        if valid_types_str:
            valid_types_str += " "
        return f"a list of {valid_types_str}values obtained from a lookup"


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
