/**
 * Copies the given text to the clipboard by temporarily creating a textarea and
 * using the documents `copy` command.
 */
export const copyToClipboard = (text) => {
  const textarea = document.createElement('textarea')
  document.body.appendChild(textarea)

  textarea.style.position = 'absolute'
  textarea.style.left = '-99999px'
  textarea.style.top = '-99999px'
  textarea.value = text
  textarea.select()

  document.execCommand('copy')
  document.body.removeChild(textarea)
}
