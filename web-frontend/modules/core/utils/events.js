export function isPrintableUnicodeCharacterKeyPress(event) {
  /*
  This function is a helper which determines whether the pressed key
  is 'not a Control Key Character'
  thereby determining if the key is a 'printable character'
   */

  if (event == null) {
    return false
  }
  const { key } = event
  const nonControlCharacterRegex = /^\P{C}$/iu
  if (nonControlCharacterRegex.test(key)) {
    return true
  }
  return false
}
