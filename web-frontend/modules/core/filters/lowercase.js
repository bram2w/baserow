/**
 * Converts a string to the same string, but with lowercase characters.
 */
export default function (value) {
  if (!value) {
    return ''
  }
  return value.toString().toLowerCase()
}
