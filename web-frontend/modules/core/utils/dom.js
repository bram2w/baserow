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

/**
 * Finds the closest scrollable parent element of the provided element.
 */
export const findScrollableParent = (element) => {
  if (element == null) {
    return null
  }

  if (element.scrollHeight > element.clientHeight) {
    return element
  } else {
    return findScrollableParent(element.parentNode)
  }
}

export const onClickOutside = (el, callback) => {
  const insideEvent = new Set()

  // Firefox and Chrome both can both have a different `target` element on `click`
  // when you release the mouse at different coordinates. Therefore we expect this
  // variable to be set on mousedown to be consistent.
  let downElement = null

  // Add the event to the `insideEvent` map. This allow to be sure a click event has
  // been triggered from an element inside this context, even if the element has
  // been removed after in the meantime.
  const clickOutsideClickEvent = (event) => {
    insideEvent.add(event)
  }
  el.addEventListener('click', clickOutsideClickEvent)

  const clickOutsideMouseDownEvent = (event) => {
    downElement = event.target
  }
  document.body.addEventListener('mousedown', clickOutsideMouseDownEvent)

  const clickOutsideEvent = (event) => {
    const target = downElement || event.target

    // If the event is from current context or any element inside current context
    // the current event should be in the insideEvent map, even if the element
    // has been removed from the DOM in the meantime
    const insideContext = insideEvent.has(event)
    if (insideContext) {
      insideEvent.delete(event)
    }

    // If the click was outside the context element because we want to ignore
    // clicks inside it or any child of this element
    if (!isElement(el, target) && !insideContext) {
      callback(target, event)
    }
  }
  document.body.addEventListener('click', clickOutsideEvent)

  return () => {
    el.removeEventListener('click', clickOutsideClickEvent)
    document.body.removeEventListener('mousedown', clickOutsideMouseDownEvent)
    document.body.removeEventListener('click', clickOutsideEvent)
  }
}

/**
 * Return whether one of the ancestors of the given node matches the given predicate.
 *
 * @param {DomElement} node The node to start the search for.
 * @param {function} predicate The predicate to test on every ancestor.
 * @param {DomElement} stop If provided, the search will stop when this element is met.
 *   It should an ancestor of the given node.
 * @returns Whether one of the ancestors matches the predicate.
 */
export const doesAncestorMatchPredicate = (node, predicate, stop) => {
  while (node != null) {
    if (stop === node) {
      return false
    }
    if (predicate(node)) {
      return true
    }
    node = node.parentNode
  }
  return false
}
