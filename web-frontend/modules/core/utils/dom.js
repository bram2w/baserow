/**
 * Checks if the target is the same as the provided element of that the element
 * contains the target. Returns true is this is the case.
 *
 * @returns boolean
 */
export const isElement = (element, target) => {
  return element !== null && (element === target || element.contains(target))
}

/**
 * Checks if the provided object is an html dom element.
 *
 * @returns boolean
 */
export const isDomElement = (obj) => {
  try {
    return obj instanceof HTMLElement
  } catch (e) {
    return (
      typeof obj === 'object' &&
      obj.nodeType === 1 &&
      typeof obj.style === 'object' &&
      typeof obj.ownerDocument === 'object'
    )
  }
}

/**
 * This function will focus a contenteditable and place the cursor at the end.
 *
 * @param element
 */
export const focusEnd = (element) => {
  const range = document.createRange()
  const selection = window.getSelection()
  range.selectNodeContents(element)
  range.collapse(false)
  selection.removeAllRanges()
  selection.addRange(range)
  element.focus()
}
