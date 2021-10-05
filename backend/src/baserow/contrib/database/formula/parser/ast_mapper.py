from decimal import Decimal
from typing import Set

from antlr4 import InputStream, CommonTokenStream
from antlr4.error.ErrorListener import ErrorListener

from baserow.contrib.database.formula.ast.tree import (
    BaserowStringLiteral,
    BaserowFunctionCall,
    BaserowIntegerLiteral,
    BaserowFieldByIdReference,
    BaserowFieldReference,
    BaserowExpression,
    BaserowDecimalLiteral,
    BaserowBooleanLiteral,
)
from baserow.contrib.database.formula.parser.exceptions import (
    InvalidNumberOfArguments,
    BaserowFormulaSyntaxError,
    MaximumFormulaSizeError,
    UnknownOperator,
    UnknownFieldByIdReference,
)
from baserow.contrib.database.formula.parser.generated.BaserowFormula import (
    BaserowFormula,
)
from baserow.contrib.database.formula.parser.generated.BaserowFormulaLexer import (
    BaserowFormulaLexer,
)
from baserow.contrib.database.formula.parser.generated.BaserowFormulaVisitor import (
    BaserowFormulaVisitor,
)
from baserow.contrib.database.formula.parser.parser import (
    convert_string_literal_token_to_string,
)
from baserow.contrib.database.formula.parser.replace_field_by_id_with_field import (
    replace_field_by_id_with_field,
)
from baserow.contrib.database.formula.parser.replace_field_with_field_by_id import (
    replace_field_with_field_by_id,
)
from baserow.contrib.database.formula.registries import formula_function_registry
from baserow.contrib.database.formula.types.formula_type import UnTyped
from baserow.core.exceptions import InstanceTypeDoesNotExist


class BaserowFormulaErrorListener(ErrorListener):
    """
    A custom error listener as ANTLR's default error listen does not raise an
    exception if a syntax error is found in a parse tree.
    """

    # noinspection PyPep8Naming
    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        msg = msg.replace("<EOF>", "the end of the formula")
        message = f"Invalid syntax at line {line}, col {column}: {msg}"
        raise BaserowFormulaSyntaxError(message)


def raw_formula_to_untyped_expression(
    formula: str, valid_field_ids: Set[int]
) -> BaserowExpression[UnTyped]:
    """
    Takes a raw user input string, syntax checks it to see if it matches the syntax of
    a Baserow Formula (raises a BaserowFormulaSyntaxError if not) and converts it into
    an untyped BaserowExpression.

    :param formula: A raw user supplied string possibly in the format of a Baserow
        Formula.
    :return: An untyped BaserowExpression which represents the provided raw formula.
    :raises BaserowFormulaSyntaxError: If the supplied formula is not in the syntax
        of the Baserow Formula language.
    """

    lexer = BaserowFormulaLexer(InputStream(formula))
    stream = CommonTokenStream(lexer)
    parser = BaserowFormula(stream)
    parser.removeErrorListeners()
    parser.addErrorListener(BaserowFormulaErrorListener())
    tree = parser.root()
    return BaserowFormulaToBaserowASTMapper(valid_field_ids).visit(tree)


def replace_field_refs_according_to_new_or_deleted_fields(
    formula: str, trash_ids_to_names, new_names_to_id
) -> str:
    """
    Given a raw formula string lexs it into a token stream and goes through and replaces
    all field_by_id references to a id in the provided trash_ids_to_names with a field
    reference of the corresponding name. Does the opposite operation with
    new_names_to_id and so will replace any field references with field_by_id according
    to the names and ids in the dict.

    This method has to work off the tokens directly as once ANTLR parses a token stream
    into a parse tree it will throw away all hidden channels, which for us are comments
    and whitespace. Because we want to directly mutate the formula string and store the
    result here we need to preserve whitespace and hence need to go off the raw tokens
    which do still include the whitespace and comments.

    :param formula: A raw formula string to transform.
    :param trash_ids_to_names: A dict of id to name to replace field_by_id(id) with
        field(name) references.
    :param new_names_to_id: A dict of name to id to replace field(name) with
        field_by_id(id) references.
    :return: A transformed formula string with field_by_id/field references substituted
        according to the input dicts. Any whitespace or comments will be preserved and
        still present in this returned formula string.
    """
    try:
        field_names_replaced_with_field_by_id = replace_field_with_field_by_id(
            formula, new_names_to_id
        )
        return replace_field_by_id_with_field(
            field_names_replaced_with_field_by_id, trash_ids_to_names
        )
    except RecursionError:
        raise MaximumFormulaSizeError()


class BaserowFormulaToBaserowASTMapper(BaserowFormulaVisitor):
    """
    A Visitor which transforms an Antlr parse tree into a BaserowExpression AST.

    Raises an UnknownBinaryOperator if the formula contains an unknown binary operator.

    Raises an UnknownFunctionDefintion if the formula has a function call to a function
    not in the registry.
    """

    def __init__(self, valid_field_ids: Set[int]):
        self.valid_field_ids = valid_field_ids

    def visitRoot(self, ctx: BaserowFormula.RootContext):
        return ctx.expr().accept(self)

    def visitStringLiteral(self, ctx: BaserowFormula.StringLiteralContext):
        # noinspection PyTypeChecker
        literal = self.process_string(ctx)
        return BaserowStringLiteral(literal, None)

    def visitDecimalLiteral(self, ctx: BaserowFormula.DecimalLiteralContext):
        return BaserowDecimalLiteral(Decimal(ctx.getText()), None)

    def visitBooleanLiteral(self, ctx: BaserowFormula.BooleanLiteralContext):
        return BaserowBooleanLiteral(ctx.TRUE() is not None, None)

    def visitBrackets(self, ctx: BaserowFormula.BracketsContext):
        return ctx.expr().accept(self)

    def process_string(self, ctx):
        literal_without_outer_quotes = ctx.getText()[1:-1]
        if ctx.SINGLEQ_STRING_LITERAL() is not None:
            literal = literal_without_outer_quotes.replace("\\'", "'")
        else:
            literal = literal_without_outer_quotes.replace('\\"', '"')
        return literal

    def visitFunctionCall(self, ctx: BaserowFormula.FunctionCallContext):
        function_name = ctx.func_name().accept(self).lower()
        function_argument_expressions = ctx.expr()

        return self._do_func(function_argument_expressions, function_name)

    def _do_func(self, function_argument_expressions, function_name):
        function_def = self._get_function_def(function_name)
        self._check_function_call_valid(function_argument_expressions, function_def)
        args = [expr.accept(self) for expr in function_argument_expressions]
        return BaserowFunctionCall[UnTyped](function_def, args, None)

    def visitBinaryOp(self, ctx: BaserowFormula.BinaryOpContext):
        if ctx.PLUS():
            op = "add"
        elif ctx.MINUS():
            op = "minus"
        elif ctx.SLASH():
            op = "divide"
        elif ctx.EQUAL():
            op = "equal"
        elif ctx.BANG_EQUAL():
            op = "not_equal"
        elif ctx.STAR():
            op = "multiply"
        elif ctx.GT():
            op = "greater_than"
        elif ctx.LT():
            op = "less_than"
        elif ctx.GTE():
            op = "greater_than_or_equal"
        elif ctx.LTE():
            op = "less_than_or_equal"
        else:
            raise UnknownOperator(ctx.getText())

        return self._do_func(ctx.expr(), op)

    @staticmethod
    def _check_function_call_valid(function_argument_expressions, function_def):
        num_expressions = len(function_argument_expressions)
        if not function_def.num_args.test(num_expressions):
            raise InvalidNumberOfArguments(function_def, num_expressions)

    @staticmethod
    def _get_function_def(function_name):
        try:
            function_def = formula_function_registry.get(function_name)
        except InstanceTypeDoesNotExist:
            raise BaserowFormulaSyntaxError(f"{function_name} is not a valid function")
        return function_def

    def visitFunc_name(self, ctx: BaserowFormula.Func_nameContext):
        return ctx.getText()

    def visitIdentifier(self, ctx: BaserowFormula.IdentifierContext):
        return ctx.getText()

    def visitIntegerLiteral(self, ctx: BaserowFormula.IntegerLiteralContext):
        return BaserowIntegerLiteral[UnTyped](int(ctx.getText()), None)

    def visitFieldReference(self, ctx: BaserowFormula.FieldReferenceContext):
        reference = ctx.field_reference()
        field_name = convert_string_literal_token_to_string(
            reference.getText(), reference.SINGLEQ_STRING_LITERAL()
        )
        return BaserowFieldReference[UnTyped](field_name, None)

    def visitFieldByIdReference(self, ctx: BaserowFormula.FieldByIdReferenceContext):
        field_id = int(str(ctx.INTEGER_LITERAL()))
        if field_id not in self.valid_field_ids:
            raise UnknownFieldByIdReference(field_id)
        return BaserowFieldByIdReference[UnTyped](field_id, None)
