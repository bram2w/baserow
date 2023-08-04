/**
 * Ensures that the value is an integer or can be converted to an integer.
 * @param {number|string} value - The value to ensure as an integer.
 * @returns {number} The value as an integer if conversion is successful.
 * @throws {Error} If the value is not a valid integer or convertible to an integer.
 */
export const ensureInteger = (value) => {
  if (Number.isInteger(value)) {
    return value
  }
  if (typeof value === 'string' || value instanceof String) {
    if (/^(-|\+)?(\d+|Infinity)$/.test(value)) {
      return Number(value)
    }
  }
  throw new Error('Value is not a valid integer or convertible to an integer.')
}

/**
 * Ensures that the value is a string or convert it.
 * @param {*} value - The value to ensure as a string.
 * @returns {string} The value as a string.
 */
export const ensureString = (value) => {
  if (value === null || value === undefined || value === '') {
    return ''
  }
  return `${value}`
}
