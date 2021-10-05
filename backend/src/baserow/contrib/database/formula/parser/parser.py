from antlr4 import InputStream
from antlr4.BufferedTokenStream import BufferedTokenStream

from baserow.contrib.database.formula.parser.generated.BaserowFormulaLexer import (
    BaserowFormulaLexer,
)


def get_token_stream_for_formula(formula: str) -> BufferedTokenStream:
    lexer = BaserowFormulaLexer(InputStream(formula))
    stream = BufferedTokenStream(lexer)
    stream.lazyInit()
    stream.fill()
    return stream


def convert_string_literal_token_to_string(string_literal, is_single_q):
    literal_without_outer_quotes = string_literal[1:-1]
    quote = "'" if is_single_q else '"'
    return literal_without_outer_quotes.replace("\\" + quote, quote)
