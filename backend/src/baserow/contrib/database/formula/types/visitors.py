from typing import Any, List, Dict, Set

from baserow.contrib.database.formula.ast.tree import (
    BaserowFunctionCall,
    BaserowStringLiteral,
    BaserowFieldReference,
    BaserowIntegerLiteral,
    BaserowFieldByIdReference,
    BaserowExpression,
    BaserowDecimalLiteral,
    BaserowBooleanLiteral,
    BaserowFunctionDefinition,
)
from baserow.contrib.database.formula.ast.visitors import BaserowFormulaASTVisitor
from baserow.contrib.database.formula.types.formula_types import (
    BaserowFormulaTextType,
    BaserowFormulaNumberType,
    BaserowFormulaBooleanType,
)
from baserow.contrib.database.formula.types.formula_type import (
    UnTyped,
    BaserowFormulaType,
    BaserowFormulaValidType,
)
from baserow.contrib.database.formula.types import table_typer


class FieldReferenceResolvingVisitor(BaserowFormulaASTVisitor[Any, List[str]]):
    def visit_field_reference(self, field_reference: BaserowFunctionCall):
        # The only time when we should encounter a field reference here is when this
        # field is pointing at a trashed or deleted field.
        return []

    def visit_string_literal(self, string_literal: BaserowStringLiteral) -> List[str]:
        return []

    def visit_boolean_literal(
        self, boolean_literal: BaserowBooleanLiteral
    ) -> List[str]:
        return []

    def visit_function_call(self, function_call: BaserowFunctionCall) -> List[str]:
        all_arg_references = []
        for expr in function_call.args:
            all_arg_references += expr.accept(self)

        return all_arg_references

    def visit_int_literal(self, int_literal: BaserowIntegerLiteral):
        return []

    def visit_decimal_literal(self, decimal_literal: BaserowDecimalLiteral):
        return []

    def visit_field_by_id_reference(
        self, field_by_id_reference: BaserowFieldByIdReference
    ):
        return [field_by_id_reference.referenced_field_id]


class FunctionsUsedVisitor(
    BaserowFormulaASTVisitor[Any, Set[BaserowFunctionDefinition]]
):
    def visit_field_reference(self, field_reference: BaserowFunctionCall):
        return set()

    def visit_string_literal(
        self, string_literal: BaserowStringLiteral
    ) -> Set[BaserowFunctionDefinition]:
        return set()

    def visit_boolean_literal(
        self, boolean_literal: BaserowBooleanLiteral
    ) -> Set[BaserowFunctionDefinition]:
        return set()

    def visit_function_call(
        self, function_call: BaserowFunctionCall
    ) -> Set[BaserowFunctionDefinition]:
        all_used_functions = {function_call.function_def}
        for expr in function_call.args:
            all_used_functions.update(expr.accept(self))

        return all_used_functions

    def visit_int_literal(
        self, int_literal: BaserowIntegerLiteral
    ) -> Set[BaserowFunctionDefinition]:
        return set()

    def visit_decimal_literal(
        self, decimal_literal: BaserowDecimalLiteral
    ) -> Set[BaserowFunctionDefinition]:
        return set()

    def visit_field_by_id_reference(
        self, field_by_id_reference: BaserowFieldByIdReference
    ) -> BaserowFunctionDefinition:
        return set()


class TypeAnnotatingASTVisitor(
    BaserowFormulaASTVisitor[UnTyped, BaserowExpression[BaserowFormulaType]]
):
    def __init__(self, field_id_to_typed_field):
        self.field_id_to_typed_field: Dict[
            int, "table_typer.TypedFieldWithReferences"
        ] = field_id_to_typed_field

    def visit_field_reference(
        self, field_reference: BaserowFieldReference[UnTyped]
    ) -> BaserowExpression[BaserowFormulaType]:
        return field_reference.with_invalid_type(
            f"references the deleted field {field_reference.referenced_field_name}"
        )

    def visit_string_literal(
        self, string_literal: BaserowStringLiteral[UnTyped]
    ) -> BaserowExpression[BaserowFormulaType]:
        return string_literal.with_valid_type(BaserowFormulaTextType())

    def visit_function_call(
        self, function_call: BaserowFunctionCall[UnTyped]
    ) -> BaserowExpression[BaserowFormulaType]:
        typed_args: List[BaserowExpression[BaserowFormulaValidType]] = []
        for expr in function_call.args:
            typed_args.append(expr.accept(self))
        return function_call.type_function_given_typed_args(typed_args)

    def visit_int_literal(
        self, int_literal: BaserowIntegerLiteral[UnTyped]
    ) -> BaserowExpression[BaserowFormulaType]:
        return int_literal.with_valid_type(
            BaserowFormulaNumberType(
                number_decimal_places=0,
            ),
        )

    def visit_decimal_literal(
        self, decimal_literal: BaserowDecimalLiteral[UnTyped]
    ) -> BaserowExpression[BaserowFormulaType]:
        return decimal_literal.with_valid_type(
            BaserowFormulaNumberType(
                number_decimal_places=decimal_literal.num_decimal_places()
            )
        )

    def visit_boolean_literal(
        self, boolean_literal: BaserowBooleanLiteral[UnTyped]
    ) -> BaserowExpression[BaserowFormulaType]:
        return boolean_literal.with_valid_type(BaserowFormulaBooleanType())

    def visit_field_by_id_reference(
        self, field_by_id_reference: BaserowFieldByIdReference[UnTyped]
    ) -> BaserowExpression[BaserowFormulaType]:
        field_id = field_by_id_reference.referenced_field_id
        if field_id in self.field_id_to_typed_field:
            updated_typed_field = self.field_id_to_typed_field[
                field_by_id_reference.referenced_field_id
            ]
            return field_by_id_reference.with_type(
                updated_typed_field.typed_expression.expression_type
            )
        else:
            return field_by_id_reference.with_invalid_type(
                f"references an unknown field with id "
                f"{field_by_id_reference.referenced_field_id}"
            )


class SubstituteFieldByIdWithThatFieldsExpressionVisitor(
    BaserowFormulaASTVisitor[Any, BaserowExpression]
):
    def visit_field_reference(self, field_reference: BaserowFieldByIdReference):
        return field_reference

    def __init__(
        self, field_id_to_typed_field: Dict[int, "table_typer.TypedFieldWithReferences"]
    ):
        self.field_id_to_typed_field = field_id_to_typed_field

    def visit_string_literal(
        self, string_literal: BaserowStringLiteral
    ) -> BaserowExpression:
        return string_literal

    def visit_function_call(
        self, function_call: BaserowFunctionCall
    ) -> BaserowExpression:
        args = [expr.accept(self) for expr in function_call.args]
        return function_call.with_args(args)

    def visit_int_literal(
        self, int_literal: BaserowIntegerLiteral
    ) -> BaserowExpression:
        return int_literal

    def visit_decimal_literal(self, decimal_literal: BaserowDecimalLiteral):
        return decimal_literal

    def visit_boolean_literal(self, boolean_literal: BaserowBooleanLiteral):
        return boolean_literal

    def visit_field_by_id_reference(
        self, field_by_id_reference: BaserowFieldByIdReference
    ) -> BaserowExpression:
        if field_by_id_reference.referenced_field_id in self.field_id_to_typed_field:
            typed_field = self.field_id_to_typed_field[
                field_by_id_reference.referenced_field_id
            ]
            return typed_field.typed_expression
        else:
            return field_by_id_reference
