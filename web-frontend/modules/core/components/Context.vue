<template>
  <div class="context" :class="{ 'visibility-hidden': !open || !updatedOnce }">
    <slot v-if="openedOnce"></slot>
  </div>
</template>

<script>
import { isElement, isDomElement } from '@baserow/modules/core/utils/dom'
import MoveToBody from '@baserow/modules/core/mixins/moveToBody'

export default {
  name: 'Context',
  mixins: [MoveToBody],
  props: {
    hideOnClickOutside: {
      type: Boolean,
      default: true,
      required: false,
    },
  },
  data() {
    return {
      open: false,
      opener: null,
      updatedOnce: false,
      // If opened once, should stay in DOM to keep nested content
      openedOnce: false,
    }
  },
  methods: {
    /**
     * Toggles the open state of the context menu.
     *
     * @param target      The original element element that changed the state of the
     *                    context, this will be used to calculate the correct position.
     * @param vertical    Bottom positions the context under the target.
     *                    Top positions the context above the target.
     *                    Over-bottom positions the context over and under the target.
     *                    Over-top positions the context over and above the target.
     * @param horizontal  `left` aligns the context with the left side of the target.
     *                    `right` aligns the context with the right side of the target.
     * @param verticalOffset
     *                    The offset indicates how many pixels the context is moved
     *                    top from the original calculated position.
     * @param horizontalOffset
     *                    The offset indicates how many pixels the context is moved
     *                    left from the original calculated position.
     * @param value       True if context must be shown, false if not and undefine
     *                    will invert the current state.
     */
    toggle(
      target,
      vertical = 'bottom',
      horizontal = 'left',
      verticalOffset = 10,
      horizontalOffset = 0,
      value
    ) {
      if (value === undefined) {
        value = !this.open
      }

      if (value) {
        this.show(
          target,
          vertical,
          horizontal,
          verticalOffset,
          horizontalOffset
        )
      } else {
        this.hide()
      }
    },
    /**
     * Calculate the position, show the context menu and register a click event on the
     * body to check if the user has clicked outside the context.
     */
    async show(
      target,
      vertical,
      horizontal,
      verticalOffset = 10,
      horizontalOffset = 0
    ) {
      const isElementOrigin = isDomElement(target)
      const updatePosition = () => {
        const css = isElementOrigin
          ? this.calculatePositionElement(
              target,
              vertical,
              horizontal,
              verticalOffset,
              horizontalOffset
            )
          : this.calculatePositionFixed(
              target,
              vertical,
              horizontal,
              verticalOffset,
              horizontalOffset
            )

        // Set the calculated positions of the context.
        for (const key in css) {
          const value = css[key] !== null ? Math.ceil(css[key]) + 'px' : 'auto'
          this.$el.style[key] = value
        }
        this.updatedOnce = true
      }

      // If we store the element who opened the context menu we can exclude the element
      // when clicked outside of this element.
      this.opener = isElementOrigin ? target : null

      this.open = true
      this.openedOnce = true

      // Delay the position update to the next tick to let the Context content
      // be available in DOM for accurate positioning.
      await this.$nextTick()
      updatePosition()

      this.$el.clickOutsideEvent = (event) => {
        if (
          // Check if the context menu is still open
          this.open &&
          // If the prop allows it to be closed by clicking outside.
          this.hideOnClickOutside &&
          // If the click was outside the context element because we want to ignore
          // clicks inside it.s
          !isElement(this.$el, event.target) &&
          // If the click was not on the opener because he can trigger the toggle
          // method.
          !isElement(this.opener, event.target) &&
          // If the click was not inside one of the context children of this context
          // menu.
          !this.moveToBody.children.some((child) => {
            return isElement(child.$el, event.target)
          })
        ) {
          this.hide()
        }
      }
      document.body.addEventListener('click', this.$el.clickOutsideEvent)

      this.$el.updatePositionEvent = (event) => {
        updatePosition()
      }
      window.addEventListener('scroll', this.$el.updatePositionEvent, true)
      window.addEventListener('resize', this.$el.updatePositionEvent)

      this.$emit('shown')
    },
    /**
     * Forces the child elements to render by setting `openedOnce` to `true`. This
     * could be useful when children of the context must be accessed before the context
     * has been opened.
     */
    forceRender() {
      this.openedOnce = true
    },
    /**
     * Hide the context menu and make sure the body event is removed.
     */
    hide(emit = true) {
      this.opener = null
      this.open = false

      if (emit) {
        this.$emit('hidden')
      }

      document.body.removeEventListener('click', this.$el.clickOutsideEvent)
      window.removeEventListener('scroll', this.$el.updatePositionEvent, true)
      window.removeEventListener('resize', this.$el.updatePositionEvent)
    },
    /**
     * Calculates the absolute position of the context based on the original clicked
     * element. If the target element is not visible, it might mean that we can't
     * figure out the correct position, so in that case we force the element to be
     * visible.
     */
    calculatePositionElement(
      target,
      vertical,
      horizontal,
      verticalOffset,
      horizontalOffset
    ) {
      const visible =
        window.getComputedStyle(target).getPropertyValue('display') !== 'none'

      // If the target is not visible then we can't calculate the position, so we
      // temporarily need to show the element forcefully.
      if (!visible) {
        target.classList.add('forced-block')
      }

      const targetRect = target.getBoundingClientRect()
      const contextRect = this.$el.getBoundingClientRect()
      const positions = { top: null, right: null, bottom: null, left: null }

      if (!visible) {
        target.classList.remove('forced-block')
      }

      // Take into account that the document might be scrollable.
      verticalOffset += document.documentElement.scrollTop
      horizontalOffset += document.documentElement.scrollLeft

      // Calculate if top, bottom, left and right positions are possible.
      const canTop = targetRect.top - contextRect.height - verticalOffset > 0
      const canBottom =
        window.innerHeight -
          targetRect.bottom -
          contextRect.height -
          verticalOffset >
        0
      const canOverTop =
        targetRect.bottom - contextRect.height - verticalOffset > 0
      const canOverBottom =
        window.innerHeight -
          targetRect.bottom -
          contextRect.height -
          verticalOffset >
        0
      const canRight =
        targetRect.right - contextRect.width - horizontalOffset > 0
      const canLeft =
        window.innerWidth -
          targetRect.left -
          contextRect.width -
          horizontalOffset >
        0

      // If bottom, top, left or right doesn't fit, but their opposite does we switch to
      // that.
      if (vertical === 'bottom' && !canBottom && canTop) {
        vertical = 'top'
      }

      if (vertical === 'top' && !canTop) {
        vertical = 'bottom'
      }

      if (vertical === 'over-bottom' && !canOverBottom && canOverTop) {
        vertical = 'over-top'
      }

      if (vertical === 'over-top' && !canOverTop) {
        vertical = 'over-bottom'
      }

      if (horizontal === 'left' && !canLeft && canRight) {
        horizontal = 'right'
      }

      if (horizontal === 'right' && !canRight) {
        horizontal = 'left'
      }

      // Calculate the correct positions for horizontal and vertical values.
      if (horizontal === 'left') {
        positions.left = targetRect.left + horizontalOffset
      }

      if (horizontal === 'right') {
        positions.right =
          window.innerWidth - targetRect.right - horizontalOffset
      }

      if (vertical === 'bottom') {
        positions.top = targetRect.bottom + verticalOffset
      }

      if (vertical === 'top') {
        positions.bottom = window.innerHeight - targetRect.top + verticalOffset
      }

      if (vertical === 'over-bottom') {
        positions.top = targetRect.top + verticalOffset
      }

      if (vertical === 'over-top') {
        positions.bottom =
          window.innerHeight - targetRect.bottom + verticalOffset
      }

      return positions
    },
    /**
     * Calculates the desired position based on the provided coordinates. For now this
     * is only used by the row context menu, but because of the reserved space of the
     * grid on the right and bottom there is always room for the context. Therefore we
     * do not need to check if the context fits.
     */
    calculatePositionFixed(coordinates) {
      return {
        left: coordinates.left,
        top: coordinates.top,
        right: null,
        bottom: null,
      }
    },
  },
}
</script>
