import abc
from typing import Generic, TypeVar

from baserow.contrib.database.formula.ast import tree

Y = TypeVar("Y")
X = TypeVar("X")


class BaserowFormulaASTVisitor(abc.ABC, Generic[Y, X]):
    @abc.abstractmethod
    def visit_string_literal(self, string_literal: "tree.BaserowStringLiteral[Y]") -> X:
        pass

    @abc.abstractmethod
    def visit_function_call(self, function_call: "tree.BaserowFunctionCall[Y]") -> X:
        pass

    @abc.abstractmethod
    def visit_int_literal(self, int_literal: "tree.BaserowIntegerLiteral[Y]") -> X:
        pass

    @abc.abstractmethod
    def visit_field_by_id_reference(
        self, field_by_id_reference: "tree.BaserowFieldByIdReference[Y]"
    ) -> X:
        pass

    @abc.abstractmethod
    def visit_field_reference(
        self, field_reference: "tree.BaserowFieldReference[Y]"
    ) -> X:
        pass

    @abc.abstractmethod
    def visit_decimal_literal(
        self, decimal_literal: "tree.BaserowDecimalLiteral[Y]"
    ) -> X:
        pass

    @abc.abstractmethod
    def visit_boolean_literal(
        self, boolean_literal: "tree.BaserowBooleanLiteral[Y]"
    ) -> X:
        pass
