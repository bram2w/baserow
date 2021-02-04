/**
 * Returns the two first characters of the provided first and last name.
 */
export default function (value) {
  if (!value) {
    return ''
  }
  const splitted = value.toString().toUpperCase().split(' ')
  return splitted.length === 1
    ? splitted[0][0]
    : splitted[0][0] + splitted[splitted.length - 1][0]
}
