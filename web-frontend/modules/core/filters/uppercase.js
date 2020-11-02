/**
 * Converts a string to the same string, but with uppercase characters.
 */
export default function (value) {
  if (!value) {
    return ''
  }
  return value.toString().toUpperCase()
}
