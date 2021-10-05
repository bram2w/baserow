import { BaserowFormulaLexer } from '@baserow/modules/database/formula/parser/generated/BaserowFormulaLexer'
import { getTokenStreamForFormula } from '@baserow/modules/database/formula/parser/parser'

/**
 * Given a map of field id to field name replaces all field_by_id references to
 * with field references. Does so whist preserving any whitespace or
 * comments. If a reference to an unknown field_by_id is made it will be left as it is.
 *
 * This algorithm is duplicated in the backend in replace_field_by_id_with_field.py
 * please sync across any changes.
 *
 * @param formula The raw string to tokenize and transform.
 * @param fieldIdToName The map of field ids to names.
 * @returns string False if the formula is not
 *    syntactically correct, otherwise the new updated formula string.
 */
export function replaceFieldByIdWithField(formula, fieldIdToName) {
  const stream = getTokenStreamForFormula(formula)

  let searchingForOpenParen = false
  let searchingForCloseParen = false
  let searchingForIntegerLiteral = false

  let newFormula = ''
  for (let i = 0; i < stream.tokens.length; i++) {
    const token = stream.tokens[i]
    let output = token.text

    const isNormalToken = token.channel === 0
    if (isNormalToken) {
      if (searchingForIntegerLiteral) {
        searchingForIntegerLiteral = false
        searchingForCloseParen = true
        if (token.type === BaserowFormulaLexer.INTEGER_LITERAL) {
          output = `'${fieldIdToName[output].replace("'", "\\'")}'`
        } else {
          // The only valid normal token is an int, we've encountered a different
          // token and hence the input string is invalid and so we'll just return it
          // untouched.
          return formula
        }
      } else if (searchingForOpenParen) {
        searchingForOpenParen = false
        if (token.type === BaserowFormulaLexer.OPEN_PAREN) {
          searchingForIntegerLiteral = true
        } else {
          return formula
        }
      } else if (searchingForCloseParen) {
        searchingForCloseParen = false
        if (token.type !== BaserowFormulaLexer.CLOSE_PAREN) {
          return formula
        }
      } else if (token.type === BaserowFormulaLexer.FIELDBYID) {
        const futureIntLiteral = _lookaheadAndFindFieldByIdIntLiteral(
          i + 1,
          stream
        )
        if (
          futureIntLiteral !== false &&
          fieldIdToName[futureIntLiteral] !== undefined
        ) {
          // Only replace field_by_id with field if we know we will find a proper int
          // referenced we know about. Otherwise we want to leave the field_by_id
          // untouched.
          searchingForOpenParen = true
          output = 'field'
        }
      }
    }

    if (token.type === BaserowFormulaLexer.EOF) {
      break
    }

    newFormula += output
  }
  return newFormula
}

function _lookaheadAndFindFieldByIdIntLiteral(start, stream) {
  let searchingForIntegerLiteral = false
  for (let i = start; i < stream.tokens.length; i++) {
    const token = stream.tokens[i]
    const isNormalToken = token.channel === 0

    if (isNormalToken) {
      if (searchingForIntegerLiteral) {
        if (token.type === BaserowFormulaLexer.INTEGER_LITERAL) {
          return parseInt(token.text)
        } else {
          return false
        }
      } else if (token.type === BaserowFormulaLexer.OPEN_PAREN) {
        searchingForIntegerLiteral = true
      } else {
        return false
      }
    }
    if (token.type === BaserowFormulaLexer.EOF) {
      return false
    }
  }
  return false
}
