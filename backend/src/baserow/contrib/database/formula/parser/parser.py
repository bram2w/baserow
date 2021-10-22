from antlr4 import InputStream, CommonTokenStream
from antlr4.BufferedTokenStream import BufferedTokenStream
from antlr4.error.ErrorListener import ErrorListener

from baserow.contrib.database.formula.parser.exceptions import BaserowFormulaSyntaxError
from baserow.contrib.database.formula.parser.generated.BaserowFormula import (
    BaserowFormula,
)
from baserow.contrib.database.formula.parser.generated.BaserowFormulaLexer import (
    BaserowFormulaLexer,
)


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


def get_token_stream_for_formula(formula: str) -> BufferedTokenStream:
    lexer = BaserowFormulaLexer(InputStream(formula))
    stream = BufferedTokenStream(lexer)
    stream.lazyInit()
    stream.fill()
    return stream


def get_parse_tree_for_formula(formula: str):
    lexer = BaserowFormulaLexer(InputStream(formula))
    stream = CommonTokenStream(lexer)
    parser = BaserowFormula(stream)
    parser.removeErrorListeners()
    parser.addErrorListener(BaserowFormulaErrorListener())
    return parser.root()


def convert_string_literal_token_to_string(string_literal, is_single_q):
    literal_without_outer_quotes = string_literal[1:-1]
    quote = "'" if is_single_q else '"'
    return literal_without_outer_quotes.replace("\\" + quote, quote)


def convert_string_to_string_literal_token(string, is_single_q):
    quote = "'" if is_single_q else '"'
    escaped = string.replace(quote, "\\" + quote)
    return quote + escaped + quote
