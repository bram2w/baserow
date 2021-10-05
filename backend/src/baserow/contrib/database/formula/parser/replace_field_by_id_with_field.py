from io import StringIO
from typing import Dict

from antlr4 import Token

from baserow.contrib.database.formula.parser.generated.BaserowFormulaLexer import (
    BaserowFormulaLexer,
)
from baserow.contrib.database.formula.parser.parser import get_token_stream_for_formula


# Translated directly from replaceFieldByIdWithField.js please keep in sync
# if changes made.
def replace_field_by_id_with_field(
    formula: str, field_id_to_name: Dict[int, str]
) -> str:
    """
    Given a baserow formula transforms any field_by_id(X) references to field(NAME)
    when there is a mapping in field_id_to_name of {X: NAME}. If no mapping is found
    then the field_by_id is left untransformed. Preserves whitespace and comments in
    the returned string.

    :param formula: A string possibly in the Baserow Formula language.
    :param field_id_to_name: A mapping of field ids to field names to replace in the
        formula.
    :return: A formula string with replacements done.
    """

    stream = get_token_stream_for_formula(formula)

    searching_for_open_paren = False
    searching_for_close_paren = False
    searching_for_integer_literal = False

    with StringIO() as buf:
        for i in range(0, len(stream.tokens)):
            t = stream.tokens[i]
            output = t.text

            is_normal_token = t.channel == 0
            if is_normal_token:
                if searching_for_integer_literal:
                    searching_for_integer_literal = False
                    searching_for_close_paren = True
                    if t.type == BaserowFormulaLexer.INTEGER_LITERAL:
                        int_literal = int(t.text)
                        field_name = field_id_to_name[int_literal]
                        escaped_field_name = field_name.replace("'", "\\'")
                        output = f"'{escaped_field_name}'"
                    else:
                        return formula
                elif searching_for_open_paren:
                    searching_for_open_paren = False
                    if t.type == BaserowFormulaLexer.OPEN_PAREN:
                        searching_for_integer_literal = True
                    else:
                        return formula
                elif searching_for_close_paren:
                    searching_for_close_paren = False
                    if t.type != BaserowFormulaLexer.CLOSE_PAREN:
                        return formula
                elif t.type == BaserowFormulaLexer.FIELDBYID:
                    looked_ahead_id = _lookahead_to_id(i + 1, stream)
                    if (
                        looked_ahead_id is not None
                        and looked_ahead_id in field_id_to_name
                    ):
                        output = "field"
                        searching_for_open_paren = True

            if t.type == Token.EOF:
                break

            buf.write(output)
        return buf.getvalue()


def _lookahead_to_id(start, stream):
    searching_for_int_literal = False
    for i in range(start, len(stream.tokens)):
        t = stream.tokens[i]
        is_normal_token = t.channel == 0
        if is_normal_token:
            if searching_for_int_literal:
                if t.type == BaserowFormulaLexer.INTEGER_LITERAL:
                    return int(t.text)
                else:
                    return None
            elif t.type == BaserowFormulaLexer.OPEN_PAREN:
                searching_for_int_literal = True
            else:
                return None
        if t.type == Token.EOF:
            return None
    return None
