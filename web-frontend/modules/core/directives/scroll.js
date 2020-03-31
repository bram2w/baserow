/**
 * A helper directive that will fire the provided binding function every time the
 * user scrolls inside an element. The reason why you would use this and not the native
 * scroll event is because the element doesn't need to have a overflow scroll. The
 * parameters of the function are going to be the change in pixels based on the
 * users scroll action.
 *
 * Example:
 * <div v-scroll="scroll" style="overflow: hidden; width: 200px; height: 200px;">
 *   <div style="width: 2000px; height: 2000px;"></div>
 * </div>
 * ...
 * methods: {
 *   scroll(pixelY, pixelX) {
 *     // Implement code here that changes the scrollTop and scrollLeft of the element.
 *   }
 * }
 *
 * @TODO this might have to made a bit more cross browser supported, but that needs
 *       to be tested.
 */
export default {
  bind(el, binding) {
    const DOM_DELTA_PIXEL = 0
    const DOM_DELTA_LINE = 1
    el.scrollDirectiveEvent = (event) => {
      event.preventDefault()

      const { deltaY, deltaX, deltaMode } = event
      let pixelY = 0
      let pixelX = 0

      // Most browsers will provide the scrolling delta as pixels.
      if (deltaMode === DOM_DELTA_PIXEL) {
        pixelY = deltaY
        pixelX = deltaX
      }

      // Firefox uses the DOM_DELTA_LINE mode when scrolling with the scrollwheel.
      if (deltaMode === DOM_DELTA_LINE) {
        pixelY = deltaY * 10
        pixelX = deltaX * 10
      }

      if (pixelY === 0 && pixelX === 0) {
        return
      }

      binding.value(pixelY, pixelX)
    }
    el.addEventListener('wheel', el.scrollDirectiveEvent)
  },
  unbind(el) {
    el.removeEventListener('wheel', el.scrollDirectiveEvent)
  },
}
