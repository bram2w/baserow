/**
 * Copies the given text to the clipboard by temporarily creating a textarea and
 * using the documents `copy` command.
 */
export const copyToClipboard = (text) => {
  navigator.clipboard.writeText(text)
}

/**
 * Values should be an object with mimetypes as key and clipboard content for this type
 * as value. This allow add the same data with multiple representation to the clipboard.
 * We can have a row saved as tsv string or as json string. Values must be strings.
 * @param {object} values object of mimetypes -> clipboard content.
 */
export const setRichClipboard = (values) => {
  const listener = (e) => {
    Object.entries(values).forEach(([type, content]) => {
      e.clipboardData.setData(type, content)
    })
    e.preventDefault()
    e.stopPropagation()
  }
  document.addEventListener('copy', listener)
  document.execCommand('copy')
  document.removeEventListener('copy', listener)
}
