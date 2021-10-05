import { BaserowFormulaLexer } from '@baserow/modules/database/formula/parser/generated/BaserowFormulaLexer'
import { getTokenStreamForFormula } from '@baserow/modules/database/formula/parser/parser'

/**
 * Given a map of old field name to new field name replaces all field references to
 * old field names with their new names. Does so whist preserving any whitespace or
 * comments. Any field references to names not in the map will be left as they are.
 *
 * @param formula The raw string to tokenize and transform.
 * @param oldFieldNameToNewFieldName The map of old name to new name.
 * @returns string The updated formula or if any invalid syntax was
 *    found the original string provided will be returned.
 */
export function updateFieldNames(formula, oldFieldNameToNewFieldName) {
  const stream = getTokenStreamForFormula(formula)

  let searchingForOpenParen = false
  let searchingForInnerFieldReferenceStringLiteral = false
  let searchingForCloseParen = false
  let newFormula = ''

  for (let i = 0; i < stream.tokens.length; i++) {
    const token = stream.tokens[i]
    let output = token.text

    // Whitespace and comments are on the hidden token channel. We ignore them entirely
    // but still output them to ensure the user doesn't loose formatting or comments
    // due to this update.
    const isNormalToken = token.channel === 0

    if (isNormalToken) {
      if (searchingForInnerFieldReferenceStringLiteral) {
        searchingForCloseParen = true
        searchingForInnerFieldReferenceStringLiteral = false
        if (token.type === BaserowFormulaLexer.SINGLEQ_STRING_LITERAL) {
          output = _replaceFieldNameInStringLiteralIfMapped(
            output,
            "'",
            oldFieldNameToNewFieldName
          )
        } else if (token.type === BaserowFormulaLexer.DOUBLEQ_STRING_LITERAL) {
          output = _replaceFieldNameInStringLiteralIfMapped(
            output,
            '"',
            oldFieldNameToNewFieldName
          )
        } else {
          // The only valid normal token is a string literal, we've encountered a
          // different token and hence the input string is invalid and so we'll just
          // return it untouched.
          return formula
        }
      } else if (searchingForOpenParen) {
        searchingForOpenParen = false
        if (token.type === BaserowFormulaLexer.OPEN_PAREN) {
          searchingForInnerFieldReferenceStringLiteral = true
        } else {
          // The only valid normal token is a (, we've encountered a different
          // token and hence the input string is invalid and so we'll just return it
          // untouched.
          return formula
        }
      } else if (searchingForCloseParen) {
        searchingForCloseParen = false
        if (token.type !== BaserowFormulaLexer.CLOSE_PAREN) {
          // The only valid normal token is a ), we've encountered a different
          // token and hence the input string is invalid and so we'll just return it
          // untouched.
          return formula
        }
      } else if (token.type === BaserowFormulaLexer.FIELD) {
        searchingForOpenParen = true
      }
    }
    if (token.type === BaserowFormulaLexer.EOF) {
      break
    }
    newFormula += output
  }
  return newFormula
}

function _replaceFieldNameInStringLiteralIfMapped(
  fieldRefStringLiteral,
  quote,
  oldFieldNameToNewFieldName
) {
  const unescapedOldName = fieldRefStringLiteral
    .replace('\\' + quote, quote)
    .slice(1, -1)

  const newName = oldFieldNameToNewFieldName[unescapedOldName]
  if (newName !== undefined) {
    const escapedNewName = newName.replace(quote, '\\' + quote)
    return quote + escapedNewName + quote
  } else {
    return fieldRefStringLiteral
  }
}
