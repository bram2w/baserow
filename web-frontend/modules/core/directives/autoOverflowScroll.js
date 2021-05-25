import ResizeObserver from 'resize-observer-polyfill'

/**
 * This directive does the same as `overflow: auto;`, so it will make sure that the
 * scrollbars are visible when the content does not fit inside the element. It
 * expects the element to have `overflow: scroll;` by default which will always show
 * the scrollbars. If the content does fit, it will add the class `prevent-scroll`
 * which adds `overflow: hidden !important;` which will remove the scrollbars.
 *
 * The reason why you would want this could be when `overflow: auto;` is causing
 * scrollbar width side effects. It could for example be that the width of the
 * element depends on the width of the children. In that case `overflow: auto;`
 * might not work as the scrollbar width is not added to the total width of the
 * element. `overflow: scroll` does add the scrollbar width.
 */
export default {
  bind(el) {
    el.autoOverflowScrollHeightObserver = new ResizeObserver(() => {
      if (el.scrollHeight <= el.clientHeight) {
        el.classList.add('prevent-scroll')
      } else {
        el.classList.remove('prevent-scroll')
      }
    })
    el.autoOverflowScrollHeightObserver.observe(el)
  },
  unbind(el) {
    el.autoOverflowScrollHeightObserver.unobserve(el)
  },
}
