/**
 * Formula autocompleting in Baserow works in two steps:
 * 1. Given a text cursor location in a formula we first figure out if it's on a
 *    function name or a field reference. Taking this name / field reference we filter
 *    down all of the possible fields and functions to just include the ones that start
 *    with that name. This is done as the user moves around the formula in the web page
 *    and the filtered functions and fields are updated and displayed in realtime.
 * 2. When a user then presses tab somewhere in the formula we use the filtered
 *    lists of fields and functions and try to insert the top field/function in this
 *    list. If it's possible we autocomplete in the field/function and move the cursor
 *    to a nice location for the user, otherwise the tab will do nothing.
 *
 * See the two functions in this file
 * calculateFilteredFunctionsAndFieldsBasedOnCursorLocation which does step 1 and
 * autocompleteFormula which does step 2 given the results of step 1.
 */
import { BaserowFormula } from '@baserow/modules/database/formula/parser/generated/BaserowFormula'
import { getTokenStreamForFormula } from '@baserow/modules/database/formula/parser/parser'
import { BaserowFormulaLexer } from '@baserow/modules/database/formula/parser/generated/BaserowFormulaLexer'

function _countRemainingOpenBrackets(i, stop, stream, numOpenBrackets) {
  for (let k = i; k < stop; k++) {
    const afterToken = stream.tokens[k]
    if (afterToken.type === BaserowFormula.OPEN_PAREN) {
      numOpenBrackets++
    }
    if (afterToken.type === BaserowFormula.CLOSE_PAREN) {
      numOpenBrackets--
    }
  }
  return numOpenBrackets
}

/**
 * Calculates the range of characters in the formula to replace given an autocomplete
 * request at cursorPosition in formula. Also returns information on if the cursor is
 * inside of a field reference or on a function identifier. Finally also returns
 * whether there is a hanging open bracket at the cursor location allowing autocomplete
 * logic to close brackets conditionally.
 *
 * @param formula The formula an autocomplete request has been made for.
 * @param cursorPosition An integer which is a valid index in the formula indicating
 *    where the users text cursor can be found in the formula.
 * @private
 */
export function _calculateAutocompleteRangeAndType(formula, cursorPosition) {
  const stream = getTokenStreamForFormula(formula)

  let searchingForFieldRefOpenParen = false
  let insideFieldRef = false
  let startPositionOfFieldRefArgument = false

  let output = ''
  let numOpenBrackets = 0

  for (let i = 0; i < stream.tokens.length; i++) {
    const token = stream.tokens[i]
    const isNormalToken = token.channel === 0

    output += token.text

    if (isNormalToken) {
      if (token.type === BaserowFormula.OPEN_PAREN) {
        numOpenBrackets++
      }
      if (token.type === BaserowFormula.CLOSE_PAREN) {
        numOpenBrackets--
      }
      if (insideFieldRef) {
        if (token.type === BaserowFormula.CLOSE_PAREN) {
          insideFieldRef = false
          startPositionOfFieldRefArgument = false
        }
      } else if (searchingForFieldRefOpenParen) {
        searchingForFieldRefOpenParen = false
        if (token.type === BaserowFormula.OPEN_PAREN) {
          insideFieldRef = true
          startPositionOfFieldRefArgument = output.length
        }
      }
      if (token.type === BaserowFormula.FIELD) {
        searchingForFieldRefOpenParen = true
      }
    }
    if (output.length >= cursorPosition) {
      const numOpenBracketsInEntireFormula = _countRemainingOpenBrackets(
        i + 1,
        stream.tokens.length,
        stream,
        numOpenBrackets
      )

      const startOfToken = output.length - token.text.length

      // Treat a field reference like a function.
      const insideFunctionRef = [
        BaserowFormulaLexer.IDENTIFIER,
        BaserowFormulaLexer.FIELD,
        BaserowFormulaLexer.IDENTIFIER_UNICODE,
      ].includes(token.type)

      // The inside of a field reference might span many tokens so we need to handle
      // those cases here, whereas a function ref will always just be one single
      // token.
      const autocompleteStartPosition = insideFieldRef
        ? startPositionOfFieldRefArgument
        : startOfToken
      const autocompleteEndPosition = insideFieldRef
        ? output.length
        : cursorPosition
      const tokenEndPosition = output.length

      return {
        insideFieldRef,
        insideFunctionRef,
        autocompleteStartPosition,
        autocompleteEndPosition,
        tokenEndPosition,
        thereIsHangingOpenBracketAtCursor: numOpenBracketsInEntireFormula !== 0,
      }
    }
  }
  return { insideFunctionRef: false, insideFieldRef: false }
}

/**
 * Calculates the text to substitute into the formula and how to shift the formula
 * given we want to do a function autocomplete.
 *
 * @param functionCandidate The function we are going to autocomplete into the formula.
 * @param cursorPosition The users text location in the formula.
 * @param autocompleteStartPosition The start of the range of characters we are
 *    replacing in the formula.
 * @param autocompleteEndPosition The end of the range of character we are replacing in
 *    the formula.
 * @param tokenEndPosition The end position of the token under the cursor.
 * @param insideFunctionRef If true the cursor is already inside a partial or fully
 *    complete function reference and we should respect it's contents and replace it
 *    when doing an autocomplete. If false we are just inserting the entire candidate
 *    at the startPosition and not doing anything fancy.
 * @private
 */
function _calculateFunctionAutocompleteResult(
  functionCandidate,
  cursorPosition,
  autocompleteStartPosition,
  autocompleteEndPosition,
  tokenEndPosition,
  insideFunctionRef
) {
  let autocompleteText = functionCandidate.value + '('
  let shiftCursorToTheRightOfAutocompleteTextBy = 0
  if (functionCandidate.value === 'field') {
    // If its the field function then we know there is only one valid argument so
    // lets be helpful by starting with the string literal populated and the cursor
    // placed inside of it.
    autocompleteText += "''"
    shiftCursorToTheRightOfAutocompleteTextBy--
  }
  if (insideFunctionRef) {
    if (cursorPosition === tokenEndPosition) {
      // Only close the function call off if the cursor is at the very end of the token
      // being autocompleted.
      autocompleteText += ')'
      shiftCursorToTheRightOfAutocompleteTextBy--
    }
    return {
      autocompleteStartPosition,
      autocompleteEndPosition,
      autocompleteText,
      shiftCursorToTheRightOfAutocompleteTextBy,
    }
  } else {
    autocompleteText += ')'
    shiftCursorToTheRightOfAutocompleteTextBy--
    return {
      autocompleteStartPosition: autocompleteStartPosition + 1,
      autocompleteEndPosition: autocompleteStartPosition + 1,
      autocompleteText,
      shiftCursorToTheRightOfAutocompleteTextBy,
    }
  }
}

/**
 * Decides if we should allow an autocomplete inside of a field reference or not.
 *
 * @param innerFieldRefText The text contained inside the field reference starting after
 *    but not including the opening paren upto but not including any close paren.
 * @param cursorPosition The users text position in the formula.
 * @param autocompleteEndPosition The end of the autocompletion range.
 * @returns {boolean} true if a field autocompletion should be done, false otherwise.
 * @private
 */
function _isCursorAtCorrectLocationInFieldRefToAutocomplete(
  innerFieldRefText,
  cursorPosition,
  autocompleteEndPosition
) {
  const endsWithQuote =
    (innerFieldRefText.endsWith("'") || innerFieldRefText.endsWith('"')) &&
    innerFieldRefText.length > 1

  // Only allow the user to place the cursor either at field(''$) or field('$') to
  // autocomplete the inside of a field.
  const cursorIsAtEnd = cursorPosition === autocompleteEndPosition
  const cursorIsAtEndOfStringLiteral =
    cursorPosition === autocompleteEndPosition - 1
  return endsWithQuote
    ? cursorIsAtEnd || cursorIsAtEndOfStringLiteral
    : cursorIsAtEnd
}

/**
 * Given we are in a formula with a range of characters we want to possibly do a field
 * reference autocomplete for this function will calculate the new field reference text
 * to autocomplete in if it is valid to do so.
 *
 * Does an autocomplete when this regex applies to the location in the formula and
 * the dollar is the cursor location:
 *    - field(['"].*$)?
 *
 * @param formula The formula to autocomplete.
 * @param autocompleteStartPosition The start of the range of characters we are possibly
 *    replacing with an autocomplete.
 * @param autocompleteEndPosition The end of the range of characters we are possibly
 *    replacing with an autocomplete.
 * @param cursorPosition The users text cursor position in the formula.
 * @param fieldCandidate The field we will be autocompleting into the formula if Ok to
 *    do so.
 * @param thereIsHangingOpenBracketAtCursor Whether or not there is a hanging open
 *    bracket at the cursor location in the formula. E.g. `field($` is true, `field($)`
 *    is false.
 * @param insideFieldRef If true the cursor is already inside a partial or fully
 *    complete field reference and we should respect it's contents and replace it
 *    when doing an autocomplete. If false we are just inserting the entire candidate
 *    at the startPosition and not doing anything fancy.
 * @private
 */
function _calculateFieldAutocompleteResult(
  formula,
  autocompleteStartPosition,
  autocompleteEndPosition,
  cursorPosition,
  fieldCandidate,
  thereIsHangingOpenBracketAtCursor,
  insideFieldRef
) {
  if (insideFieldRef) {
    const innerFieldRef = formula.slice(
      autocompleteStartPosition,
      autocompleteEndPosition
    )
    const startsWithDoubleQuote = innerFieldRef.startsWith('"')
    const startsWithSingleQuote = innerFieldRef.startsWith("'")
    // Allow completing inside of a field ref with no text like `field($)` but disallow
    // any syntactically incorrect refs like `field(a$`.
    const innerFieldRefCorrectlyStartsWithQuoteOrIsEmpty =
      innerFieldRef.length === 0 ||
      startsWithSingleQuote ||
      startsWithDoubleQuote
    if (innerFieldRefCorrectlyStartsWithQuoteOrIsEmpty) {
      if (
        _isCursorAtCorrectLocationInFieldRefToAutocomplete(
          innerFieldRef,
          cursorPosition,
          autocompleteEndPosition
        )
      ) {
        let autocompleteText = _fieldNameToStringLiteral(
          startsWithDoubleQuote,
          fieldCandidate.value
        )

        let shiftCursorToTheRightOfAutocompleteTextBy = 0
        if (thereIsHangingOpenBracketAtCursor) {
          autocompleteText += ')'
        } else {
          // There is already a closing bracket for this field(..) so we need to shift
          // one past it to place the cursor after the field ref like so: field(..)$
          shiftCursorToTheRightOfAutocompleteTextBy = 1
        }

        return {
          autocompleteStartPosition,
          autocompleteEndPosition,
          autocompleteText,
          shiftCursorToTheRightOfAutocompleteTextBy,
        }
      }
    }
  } else {
    const autocompleteText =
      'field(' + _fieldNameToStringLiteral(false, fieldCandidate.value) + ')'

    return {
      autocompleteStartPosition: autocompleteStartPosition + 1,
      autocompleteEndPosition: autocompleteStartPosition + 1,
      autocompleteText,
      shiftCursorToTheRightOfAutocompleteTextBy: 0,
    }
  }
  return false
}

/**
 * Given a formula and a users text cursor position in said formula calculates and
 * returns a result object containing the information to do an autocomplete on that
 * formula.
 *
 *
 * @param formula The formula autocompletion is being checked for.
 * @param cursorPosition The users text position inside the formula.
 *    autocomplete and a field is provided here then its name will be autocompleted in.
 * @param functionCandidate If the users cursor is in a valid place to do a function
 *    autocomplete and a function is provided here then its function type will be
 *    autocompleted in.
 * @param fieldCandidate If the users cursor is in a valid place to do a field reference
 * @returns Object An object with the following properties:
 *    - autocompleteStartLocation : The index into the formula where to start replacing
 *        text.
 *    - autocompleteEndLocation : The index into the formula where to stop replacing
 *        text.
 *    - autocompleteText: The text to substitute into the range of text removed from the
 *        formula indicated by the start/end locations.
 *    - shiftCursorToTheRightOfAutocompleteTextBy: A number to indicate how to shift
 *        the users cursor after an autocomplete has been done. This is relative to the
 *        end of where the new autocompleteText ends up in the formula.
 * @private
 */
export function _calculateAutocompleteLocationAndText(
  formula,
  cursorPosition,
  functionCandidate,
  fieldCandidate
) {
  const {
    insideFieldRef,
    insideFunctionRef,
    autocompleteStartPosition,
    autocompleteEndPosition,
    thereIsHangingOpenBracketAtCursor,
    tokenEndPosition,
  } = _calculateAutocompleteRangeAndType(formula, cursorPosition)

  if (fieldCandidate) {
    const fieldAutocompleteResultOrFalse = _calculateFieldAutocompleteResult(
      formula,
      autocompleteStartPosition,
      autocompleteEndPosition,
      cursorPosition,
      fieldCandidate,
      thereIsHangingOpenBracketAtCursor,
      insideFieldRef
    )
    if (fieldAutocompleteResultOrFalse) {
      return fieldAutocompleteResultOrFalse
    }
  } else if (functionCandidate) {
    return _calculateFunctionAutocompleteResult(
      functionCandidate,
      cursorPosition,
      autocompleteStartPosition,
      autocompleteEndPosition,
      tokenEndPosition,
      insideFunctionRef
    )
  }
  // No valid autocomplete, return values which result in nothing happening.
  return {
    autocompleteStartPosition: cursorPosition,
    autocompleteEndPosition: cursorPosition,
    autocompleteText: '',
    shiftCursorToTheRightOfAutocompleteTextBy: 0,
  }
}

function _fieldNameToStringLiteral(doubleQuote, fieldName) {
  const quote = doubleQuote ? '"' : "'"
  const escapedFieldName = fieldName.replace(quote, '\\' + quote)
  return quote + escapedFieldName + quote
}

/**
 * Given a formula and a cursor position in it calculates a new formula with the token
 * at the cursor autocompleted based on a list of filtered functions and fields.
 *
 * @param formula The formula to autocomplete
 * @param startingCursorLocation A location inside the formula where to trigger
 *    autocompletion.
 * @param functionCandidate The best autocomplete candidate for a function.
 * @param fieldCandidate The best autocomplete candidate for a field.
 * @returns {{newCursorPosition: *, autocompletedFormula: string}|{newCursorPosition, autocompletedFormula}}
 *    Returns a formula which has had an autocompletion done if one made sense and a
 *    new location to move the cursor to in the formula. If no autocompletion occurred
 *    then the same formula and location will be returned.
 */
export function autocompleteFormula(
  formula,
  startingCursorLocation,
  functionCandidate,
  fieldCandidate
) {
  const {
    autocompleteStartPosition,
    autocompleteEndPosition,
    autocompleteText,
    shiftCursorToTheRightOfAutocompleteTextBy,
  } = _calculateAutocompleteLocationAndText(
    formula,
    startingCursorLocation,
    functionCandidate,
    fieldCandidate
  )

  const formulaUptoStart = formula.slice(0, autocompleteStartPosition)
  const formulaAfterEnd = formula.slice(autocompleteEndPosition)

  const autocompletedFormula =
    formulaUptoStart + autocompleteText + formulaAfterEnd
  const newCursorPosition =
    formulaUptoStart.length +
    autocompleteText.length +
    shiftCursorToTheRightOfAutocompleteTextBy
  return { autocompletedFormula, newCursorPosition }
}

function _filterFieldsByStringLiteral(tokenTextUptoCursor, fields) {
  // Get rid of the quote in the front
  const withoutFrontQuote = tokenTextUptoCursor.slice(1)
  let fieldFilter = ''
  if (withoutFrontQuote.endsWith("'") || withoutFrontQuote.endsWith('"')) {
    // Strip off the final quote if it exists
    fieldFilter = withoutFrontQuote.slice(0, withoutFrontQuote.length - 1)
  } else {
    // Allow filtering on incomplete fields like `field('aaa` shoudl result in a
    // filter of 'aaa'.
    fieldFilter = withoutFrontQuote
  }
  return fields.filter((f) => f.value.startsWith(fieldFilter))
}

/**
 * Given a formula and a location of a cursor in the formula uses the token present at
 * the location to filter down the provided lists of fields and functions.
 *
 * For example if the cursor is on a function name then will return no fields and a
 * only functions which start with that function name and vice versa for fields.
 *
 * @param formula The formula where the cursor is in.
 * @param cursorLocation The location of the cursor in the formula.
 * @param fields An unfiltered list of all possible fields in the formula.
 * @param functions An unfiltered list of all possible functions.
 * @returns {{filteredFields, filtered: boolean, filteredFunctions: *[]}|{filteredFields, filtered: boolean, filteredFunctions}|{filteredFields: *[], filtered: boolean, filteredFunctions}}
 *    Returns the lists filtered based on the cursor location and a boolean indicating
 *    if a filter was done or not. If no filter was done then the same lists will be
 *    returned unfiltered.
 */
export function calculateFilteredFunctionsAndFieldsBasedOnCursorLocation(
  formula,
  cursorLocation,
  fields,
  functions
) {
  const { insideFieldRef, insideFunctionRef, autocompleteStartPosition } =
    _calculateAutocompleteRangeAndType(formula, cursorLocation)

  const tokenTextUptoCursor = formula.slice(
    autocompleteStartPosition,
    cursorLocation
  )

  let filteredFields = fields
  let filteredFunctions = functions
  let filtered = false

  if (insideFieldRef) {
    filteredFields = _filterFieldsByStringLiteral(tokenTextUptoCursor, fields)
    filteredFunctions = []
    filtered = true
  } else if (insideFunctionRef) {
    filteredFunctions = functions.filter((f) =>
      f.value.startsWith(tokenTextUptoCursor)
    )
    filteredFields = []
    filtered = true
  }
  return {
    filteredFields,
    filteredFunctions,
    filtered,
  }
}
