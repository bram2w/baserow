from typing import Any, Set, List

from baserow.contrib.database.fields.dependencies.exceptions import (
    SelfReferenceFieldDependencyError,
)
from baserow.contrib.database.fields.dependencies.types import FieldDependencies
from baserow.contrib.database.formula.ast.tree import (
    BaserowFunctionCall,
    BaserowStringLiteral,
    BaserowFieldReference,
    BaserowIntegerLiteral,
    BaserowDecimalLiteral,
    BaserowBooleanLiteral,
    BaserowFunctionDefinition,
)
from baserow.contrib.database.formula.ast.visitors import BaserowFormulaASTVisitor
from baserow.contrib.database.formula.types.formula_type import (
    UnTyped,
    BaserowFormulaValidType,
)
from baserow.contrib.database.formula.types.formula_types import (
    BaserowExpression,
    BaserowFormulaType,
    BaserowFormulaTextType,
    BaserowFormulaNumberType,
    BaserowFormulaBooleanType,
)


class FunctionsUsedVisitor(
    BaserowFormulaASTVisitor[Any, Set[BaserowFunctionDefinition]]
):
    def visit_field_reference(self, field_reference: BaserowFieldReference):
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


class FieldReferenceExtractingVisitor(
    BaserowFormulaASTVisitor[UnTyped, FieldDependencies]
):
    """
    Calculates and returns all the field dependencies that the baserow expression has.
    """

    def __init__(self, table, field_lookup_cache):
        self.field_lookup_cache = field_lookup_cache
        self.table = table

    def visit_field_reference(
        self, field_reference: BaserowFieldReference[UnTyped]
    ) -> FieldDependencies:
        if field_reference.target_field is None:
            field = self.field_lookup_cache.lookup_by_name(
                self.table, field_reference.referenced_field_name
            )
            from baserow.contrib.database.fields.models import LinkRowField

            if field is not None and isinstance(field, LinkRowField):
                primary_field = field.get_related_primary_field()
                return {
                    (
                        field_reference.referenced_field_name,
                        primary_field.name if primary_field is not None else "unknown",
                    )
                }

            return {field_reference.referenced_field_name}
        else:
            return {
                (
                    field_reference.referenced_field_name,
                    field_reference.target_field,
                )
            }

    def visit_string_literal(
        self, string_literal: BaserowStringLiteral[UnTyped]
    ) -> FieldDependencies:
        return set()

    def visit_function_call(
        self, function_call: BaserowFunctionCall[UnTyped]
    ) -> FieldDependencies:
        field_references: FieldDependencies = set()
        for expr in function_call.args:
            field_references.update(expr.accept(self))
        return field_references

    def visit_int_literal(
        self, int_literal: BaserowIntegerLiteral[UnTyped]
    ) -> FieldDependencies:
        return set()

    def visit_decimal_literal(
        self, decimal_literal: BaserowDecimalLiteral[UnTyped]
    ) -> FieldDependencies:
        return set()

    def visit_boolean_literal(
        self, boolean_literal: BaserowBooleanLiteral[UnTyped]
    ) -> FieldDependencies:
        return set()


class FormulaTypingVisitor(
    BaserowFormulaASTVisitor[UnTyped, BaserowExpression[BaserowFormulaType]]
):
    def __init__(self, field_being_typed, field_lookup_cache):
        self.field_lookup_cache = field_lookup_cache
        self.field_being_typed = field_being_typed

    def visit_field_reference(
        self, field_reference: BaserowFieldReference[UnTyped]
    ) -> BaserowExpression[BaserowFormulaType]:
        from baserow.contrib.database.fields.registries import field_type_registry

        referenced_field_name = field_reference.referenced_field_name
        if referenced_field_name == self.field_being_typed.name:
            raise SelfReferenceFieldDependencyError()

        table = self.field_being_typed.table
        referenced_field = self.field_lookup_cache.lookup_by_name(
            table, referenced_field_name
        )
        if referenced_field is None:
            return field_reference.with_invalid_type(
                f"references the deleted or unknown field"
                f" {field_reference.referenced_field_name}"
            )
        else:
            field_type = field_type_registry.get_by_model(referenced_field)
            target_field = field_reference.target_field
            if target_field is not None:
                from baserow.contrib.database.fields.models import LinkRowField

                if not isinstance(referenced_field, LinkRowField):
                    return field_reference.with_invalid_type(
                        "first lookup function argument must be a link row field"
                    )
                target_table = referenced_field.link_row_table

                target_field = self.field_lookup_cache.lookup_by_name(
                    target_table, target_field
                )
                if target_field is None:
                    return field_reference.with_invalid_type(
                        f"references the deleted or unknown field"
                        f" {field_reference.target_field} in table "
                        f"{target_table.name}"
                    )
                else:
                    return self._create_lookup_reference(
                        target_field, referenced_field, field_reference
                    )
            # check the lookup field
            expression = field_type.to_baserow_formula_expression(referenced_field)
            if isinstance(expression, BaserowFunctionCall):
                expression = expression.expression_type.unwrap_at_field_level(
                    expression
                )
            return expression

    def _create_lookup_reference(self, target_field, referenced_field, field_reference):
        from baserow.contrib.database.fields.registries import field_type_registry
        from baserow.contrib.database.fields.models import LinkRowField

        lookup_field_type = field_type_registry.get_by_model(target_field)
        formula_type = lookup_field_type.to_baserow_formula_type(target_field)
        if isinstance(target_field, LinkRowField):
            # If we are looking up a link row field we need to do an
            # extra relational jump to that primary field.
            related_primary_field = target_field.get_related_primary_field()
            if related_primary_field is None:
                return field_reference.with_invalid_type(
                    "references a deleted or unknown table"
                )
            sub_ref = "__" + related_primary_field.db_column
        else:
            sub_ref = ""
        return BaserowFieldReference(
            referenced_field.db_column,
            target_field.db_column + sub_ref,
            formula_type,
        )

    def visit_string_literal(
        self, string_literal: BaserowStringLiteral[UnTyped]
    ) -> BaserowExpression[BaserowFormulaType]:
        return string_literal.with_valid_type(BaserowFormulaTextType())

    def visit_function_call(
        self, function_call: BaserowFunctionCall[UnTyped]
    ) -> BaserowExpression[BaserowFormulaType]:
        typed_args: List[BaserowExpression[BaserowFormulaValidType]] = []
        requires_aggregate_wrapper = []
        for index, expr in enumerate(function_call.args):
            arg_expr = expr.accept(self)
            if arg_expr.requires_aggregate_wrapper:
                requires_aggregate_wrapper.append(str(index + 1))
            typed_args.append(arg_expr)

        if requires_aggregate_wrapper and not function_call.function_def.aggregate:
            plural_s = (
                "s numbered" if len(requires_aggregate_wrapper) > 1 else " number"
            )
            return function_call.with_invalid_type(
                f"input{plural_s} {','.join(requires_aggregate_wrapper)} to"
                f" {function_call.function_def} must be directly wrapped by an "
                f"aggregate function like sum, avg, count etc"
            )
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
