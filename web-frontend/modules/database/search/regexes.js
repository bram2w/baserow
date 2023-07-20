/***
 * These regexes must be kept in sync with the python ones in
 * backend/src/baserow/contrib/database/search/regexes.py. Please see that file for
 * more detail on what these regexes are being used for.
 */

function getSearchRegex() {
  const RE_DASH_NOT_FOLLOWED_BY_DIGIT = '-(?!\\d)'
  const RE_STANDALONE_DASH = '\\b-\\b'
  // The backend RE_DASH_PRECEDED_BY_NON_WHITESPACE_AND_FOLLOWED_BY_DIGIT is
  // implemented by a second replace call
  const RE_MATCH_ALL_DASH_OTHER_THAN_NEGATIVE_NUMBERS_AND_DECIMAL_NUMBERS = [
    RE_DASH_NOT_FOLLOWED_BY_DIGIT,
    RE_STANDALONE_DASH,
  ].join('|')

  // Note that \w in python is translated the equivilant unicode word matching javascript
  // regex \\p{L}\\p{M}
  const RE_ALL_NON_WHITESPACE_OR_WORD_CHARACTERS_EXCLUDING_DASH =
    '[^\\p{L}\\p{M}\\p{N}\\s\\-]'
  return new RegExp(
    [
      RE_ALL_NON_WHITESPACE_OR_WORD_CHARACTERS_EXCLUDING_DASH,
      '_',
      RE_MATCH_ALL_DASH_OTHER_THAN_NEGATIVE_NUMBERS_AND_DECIMAL_NUMBERS,
    ].join('|'),
    'gu'
  )
}

export function convertStringToMatchBackendTsvectorData(inputString) {
  if (inputString === null || inputString === undefined) {
    return ''
  }
  const RE_ONE_OR_MORE_WHITESPACE = /\s+/g
  // Some browsers don't support look behinds so use a replace with capture groups
  // instead.
  const RE_DASH_PRECEDED_BY_NON_WHITESPACE_AND_FOLLOWED_BY_DIGIT = /(\S)-(\d)/gu
  const initialTrimmedLoweredInputString = inputString
    .toString()
    .trim()
    .toLowerCase()
  const punctuationStrippedValueMatchingBackendTsvColumnData =
    initialTrimmedLoweredInputString
      .replace(getSearchRegex(), ' ')
      .replace(
        RE_DASH_PRECEDED_BY_NON_WHITESPACE_AND_FOLLOWED_BY_DIGIT,
        '$1 $2'
      )
      .toLowerCase()
  return punctuationStrippedValueMatchingBackendTsvColumnData
    .replace(RE_ONE_OR_MORE_WHITESPACE, ' ')
    .trim()
}
