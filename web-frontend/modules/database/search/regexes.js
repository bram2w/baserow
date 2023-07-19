/***
 * These regexes must be kept in sync with the python ones in
 * backend/src/baserow/contrib/database/search/regexes.py. Please see that file for
 * more detail on what these regexes are being used for.
 */

const RE_ONE_OR_MORE_WHITESPACE = /\s+/g
const RE_DASH_OR_DOT_NOT_FOLLOWED_BY_DIGIT = '[-.](?!\\d)'
const RE_DASH_OR_DOT_PRECEDED_BY_NON_WHITESPACE_AND_FOLLOWED_BY_DIGIT =
  '(?<=\\S)[-\\.](?=\\d)'
const RE_STANDALONE_DASH = '\\b-\\b'
const RE_MATCH_ALL_DASH_AND_DOTS_OTHER_THAN_NEGATIVE_NUMBERS_AND_DECIMAL_NUMBERS =
  [
    RE_DASH_OR_DOT_NOT_FOLLOWED_BY_DIGIT,
    RE_DASH_OR_DOT_PRECEDED_BY_NON_WHITESPACE_AND_FOLLOWED_BY_DIGIT,
    RE_STANDALONE_DASH,
  ].join('|')

// Note that \w in python is translated the equivilant unicode word matching javascript
// regex \\p{L}\\p{M}
const RE_ALL_NON_WHITESPACE_OR_WORD_CHARACTERS_EXCLUDING_DASH_OR_DOT =
  '[^\\p{L}\\p{M}\\p{N}\\s\\-.]'
const RE_REMOVE_ALL_PUNCTUATION_ALREADY_REMOVED_FROM_TSVS_FOR_QUERY =
  new RegExp(
    [
      RE_ALL_NON_WHITESPACE_OR_WORD_CHARACTERS_EXCLUDING_DASH_OR_DOT,
      '_',
      RE_MATCH_ALL_DASH_AND_DOTS_OTHER_THAN_NEGATIVE_NUMBERS_AND_DECIMAL_NUMBERS,
    ].join('|'),
    'gu'
  )

export function convertStringToMatchBackendTsvectorData(inputString) {
  if (inputString === null || inputString === undefined) {
    return ''
  }
  const initialTrimmedLoweredInputString = inputString
    .toString()
    .trim()
    .toLowerCase()
  const punctuationStrippedValueMatchingBackendTsvColumnData =
    initialTrimmedLoweredInputString
      .replace(
        RE_REMOVE_ALL_PUNCTUATION_ALREADY_REMOVED_FROM_TSVS_FOR_QUERY,
        ' '
      )
      .toLowerCase()
  return punctuationStrippedValueMatchingBackendTsvColumnData
    .replace(RE_ONE_OR_MORE_WHITESPACE, ' ')
    .trim()
}
