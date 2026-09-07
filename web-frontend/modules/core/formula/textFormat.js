/**
 * The text format of a user-provided text is stored inside the value itself: a
 * value that begins with the Markdown sentinel below is rendered as Markdown by
 * the Application Builder. The sentinel is part of the *stored* value only, it
 * is never part of the formula syntax, never resolved, never validated and
 * never displayed. Every consumer goes through the helpers of this module,
 * nothing else should compare against the literal.
 *
 * The value is either a formula string (the sentinel goes in front of the
 * formula, e.g. `__markdown__get('data_source.1.field_2')`) or a plain string
 * such as a collection field name or a choice option name.
 */

export const TEXT_FORMATS = {
  PLAIN: 'plain',
  MARKDOWN: 'markdown',
}

export const MARKDOWN_PREFIX = '__markdown__'

/**
 * Splits a stored value into its text format and the bare value.
 *
 * @param {string|any} value The stored value, with or without the sentinel.
 * @returns {{format: string, value: any}} The format and the bare value.
 *   Non-string values are returned unchanged with the `plain` format.
 */
export const splitFormat = (value) => {
  if (typeof value === 'string' && value.startsWith(MARKDOWN_PREFIX)) {
    return {
      format: TEXT_FORMATS.MARKDOWN,
      value: value.slice(MARKDOWN_PREFIX.length),
    }
  }
  return { format: TEXT_FORMATS.PLAIN, value }
}

/**
 * Returns the bare value, without the sentinel if it has one.
 */
export const stripFormat = (value) => splitFormat(value).value

/**
 * Returns the text format of a stored value.
 */
export const getFormat = (value) => splitFormat(value).format

/**
 * Marks a bare value with the given text format.
 *
 * @param {string} bareValue The value without any text format marker.
 * @param {string} format The text format the value should be rendered with.
 * @returns {string} The stored representation of the value.
 */
export const addPrefix = (bareValue, format = TEXT_FORMATS.MARKDOWN) =>
  format === TEXT_FORMATS.MARKDOWN
    ? `${MARKDOWN_PREFIX}${bareValue ?? ''}`
    : bareValue

/**
 * Changes the text format of a stored value, keeping its bare value.
 */
export const setFormat = (value, format) =>
  addPrefix(stripFormat(value), format)

/**
 * Returns the text format of a formula object (`{ formula, mode, version }`).
 */
export const getFormulaFormat = (formulaObject) =>
  getFormat(formulaObject?.formula)

/**
 * Returns a copy of the formula object with the given text format.
 */
export const setFormulaFormat = (formulaObject, format) => ({
  ...(formulaObject || {}),
  formula: setFormat(formulaObject?.formula ?? '', format),
})
