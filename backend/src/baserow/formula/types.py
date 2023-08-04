from abc import ABC, abstractmethod
from typing import Any, List

FormulaArg = Any
FormulaArgs = List[FormulaArg]


class FormulaContext(ABC):
    @abstractmethod
    def __getitem__(self, key: str) -> Any:
        """
        A dict like object as formula context.
        """


class FunctionCollection(ABC):
    @abstractmethod
    def get(self, name: str):
        """
        Needs to return a function given the name of the function
        :param name: The name of the function
        :return: The function itself
        """


class FormulaFunction(ABC):
    @abstractmethod
    def validate_args(args: FormulaArgs):
        """Should validate the given arguments."""

    @abstractmethod
    def parse_args(args: FormulaArgs) -> FormulaArgs:
        """
        Should return the parsed arguments.
        """

    @abstractmethod
    def execute(context: FormulaContext, args: FormulaArgs) -> Any:
        """Executes the function"""
