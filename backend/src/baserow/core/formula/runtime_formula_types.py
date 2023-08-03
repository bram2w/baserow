import abc
from typing import List, Optional

from baserow.core.registry import Instance
from baserow.core.utils import get_nested_value_from_dict
from baserow.formula.parser.exceptions import (
    InvalidFormulaArgumentType,
    InvalidNumberOfArguments,
)
from baserow.formula.types.argument_types import (
    BaserowRuntimeFormulaArgumentType,
    NumberBaserowRuntimeFormulaArgumentType,
    TextBaserowRuntimeFormulaArgumentType,
)
from baserow.formula.types.types import (
    RuntimeFormulaArg,
    RuntimeFormulaArgs,
    RuntimeFormulaContext,
)


class RuntimeFormulaFunction(abc.ABC, Instance):
    @classmethod
    @property
    @abc.abstractmethod
    def type(cls) -> str:
        """
        Should be a unique lowercase string used to identify this type.
        """

        pass

    @property
    def args(self) -> Optional[List[BaserowRuntimeFormulaArgumentType]]:
        """
        Should define the arguments the function has. If null then we don't know what
        arguments the function has any anything is accepted.

        :return: The arguments configuration that is expected by the execute function
        """

        return None

    @property
    def num_args(self):
        """
        Should define the number of arguments expected when they execute function.

        :return: The number of arguments that are expected
        """

        return None if self.args is None else len(self.args)

    @abc.abstractmethod
    def execute(self, context: RuntimeFormulaContext, args: RuntimeFormulaArgs):
        """
        This is the main function that will produce a result for the defined formula

        :return: Result of executing the formula
        """

        pass

    def validate_args(self, args: RuntimeFormulaArgs):
        """
        This function can be called to validate all arguments given to the formula

        :param args: The arguments provided to the formula
        :raises InvalidNumberOfArguments: If the number of arguments is invalid
        :raises InvalidFormulaArgumentType: If any of the arguments have a wrong type
        """

        if not self.validate_number_of_args(args):
            raise InvalidNumberOfArguments(self, args)
        invalid_arg = self.validate_type_of_args(args)
        if invalid_arg:
            raise InvalidFormulaArgumentType(self, invalid_arg)

    def validate_number_of_args(self, args: RuntimeFormulaArgs) -> bool:
        """
        This function validates that the number of args is correct.

        :param args: The args passed to the execute function
        :return: If the number of arguments is correct
        """

        return self.num_args is None or len(args) <= self.num_args

    def validate_type_of_args(
        self, args: RuntimeFormulaArgs
    ) -> Optional[RuntimeFormulaArg]:
        """
        This function validates that the type of all args is correct.
        If a type is incorrect it will return that arg.

        :param args: The args that are being checked
        :return: The arg that has the wrong type, if any
        """

        if self.args is None:
            return None

        return next(
            (
                arg
                for arg, index in zip(args, range(len(args)))
                if not self.args[index].test(arg)
            ),
            None,
        )

    def parse_args(self, args: RuntimeFormulaArgs) -> RuntimeFormulaArgs:
        """
        This function parses the arguments before they get handed over to the execute
        function. This allows us to cast any args that might be of the wrong type to
        the correct type or transform the data in any other way we wish to.

        :param args: The args that are being parsed
        """

        if self.args is None:
            return args

        return [
            self.args[index].parse(arg) for arg, index in zip(args, range(len(args)))
        ]


class RuntimeConcat(RuntimeFormulaFunction):
    type = "concat"

    def execute(self, context: RuntimeFormulaContext, args: RuntimeFormulaArgs):
        return "".join([str(a) for a in args])

    def validate_number_of_args(self, args):
        return len(args) >= 2


class RuntimeGet(RuntimeFormulaFunction):
    type = "get"
    args = [TextBaserowRuntimeFormulaArgumentType()]

    def execute(self, context: RuntimeFormulaContext, args: RuntimeFormulaArgs):
        return get_nested_value_from_dict(context, args[0])


class RuntimeAdd(RuntimeFormulaFunction):
    type = "add"
    args = [
        NumberBaserowRuntimeFormulaArgumentType(),
        NumberBaserowRuntimeFormulaArgumentType(),
    ]

    def execute(self, context: RuntimeFormulaContext, args: RuntimeFormulaArgs):
        return args[0] + args[1]
