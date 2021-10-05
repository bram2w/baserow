from io import StringIO
from typing import Dict

from antlr4 import Token

from baserow.contrib.database.formula.ast.exceptions import UnknownFieldReference
from baserow.contrib.database.formula.parser.generated.BaserowFormulaLexer import (
    BaserowFormulaLexer,
)
from baserow.contrib.database.formula.parser.parser import (
    get_token_stream_for_formula,
    convert_string_literal_token_to_string,
)


def _replace_field_name_in_string_literal_or_raise_if_unknown(
    field_ref_string_literal: str,
    is_single_q: bool,
    field_name_to_field_id: Dict[str, int],
) -> str:
    unescaped_old_name = convert_string_literal_token_to_string(
        field_ref_string_literal, is_single_q
    )

    field_id = field_name_to_field_id.get(unescaped_old_name, None)
    if field_id is not None:
        return str(field_id)
    else:
        raise UnknownFieldReference(unescaped_old_name)


def replace_field_with_field_by_id(
    formula: str, field_name_to_field_id: Dict[str, int]
) -> str:
    """
    Given a baserow formula transforms any field(NAME) references to field_by_id(X)
    when there is a mapping in field_name_to_field_id of {NAME: X}. If no mapping is
    found then a UnknownFieldReference exception is raised. Preserves whitespace and
    comments in the returned string.

    :param formula: A string possibly in the Baserow Formula language.
    :param field_name_to_field_id: A mapping of field names to field ids to replace in
        the formula.
    :return: A formula string with replacements done.
    :raises UnknownFieldReference: When a field(NAME) is found in the formula but NAME
        is not present in field_name_to_field_id.
    """

    stream = get_token_stream_for_formula(formula)

    searching_for_open_paren = False
    searching_for_inner_field_reference_string_literal = False
    searching_for_close_paren = False

    with StringIO() as buf:
        for i in range(0, len(stream.tokens)):
            t = stream.tokens[i]
            output = t.text
            is_normal_token = t.channel == 0
            if is_normal_token:
                if searching_for_inner_field_reference_string_literal:
                    searching_for_inner_field_reference_string_literal = False
                    searching_for_close_paren = True
                    if t.type == BaserowFormulaLexer.SINGLEQ_STRING_LITERAL:
                        output = (
                            _replace_field_name_in_string_literal_or_raise_if_unknown(
                                output, True, field_name_to_field_id
                            )
                        )
                    elif t.type == BaserowFormulaLexer.DOUBLEQ_STRING_LITERAL:
                        output = (
                            _replace_field_name_in_string_literal_or_raise_if_unknown(
                                output, False, field_name_to_field_id
                            )
                        )
                    else:
                        return formula
                elif searching_for_open_paren:
                    searching_for_open_paren = False
                    if t.type == BaserowFormulaLexer.OPEN_PAREN:
                        searching_for_inner_field_reference_string_literal = True
                    else:
                        return formula
                elif searching_for_close_paren:
                    searching_for_close_paren = False
                    if t.type != BaserowFormulaLexer.CLOSE_PAREN:
                        return formula
                elif t.type == BaserowFormulaLexer.FIELD:
                    future_string_literal = _lookahead_to_name(i + 1, stream)
                    if (
                        future_string_literal is not None
                        and future_string_literal in field_name_to_field_id
                    ):
                        searching_for_open_paren = True
                        output = "field_by_id"

            if t.type == Token.EOF:
                break

            buf.write(output)
        return buf.getvalue()


def _lookahead_to_name(start, stream):
    searching_for_string_literal = False
    for i in range(start, len(stream.tokens)):
        t = stream.tokens[i]
        is_normal_token = t.channel == 0
        if is_normal_token:
            if searching_for_string_literal:
                if t.type == BaserowFormulaLexer.SINGLEQ_STRING_LITERAL:
                    return convert_string_literal_token_to_string(t.text, True)
                elif t.type == BaserowFormulaLexer.DOUBLEQ_STRING_LITERAL:
                    return convert_string_literal_token_to_string(t.text, False)
                else:
                    return None
            elif t.type == BaserowFormulaLexer.OPEN_PAREN:
                searching_for_string_literal = True
            else:
                return None
        if t.type == Token.EOF:
            return None
    return None
