<script>
import Dropdown from '@baserow/modules/core/components/Dropdown'
import dropdown from '@baserow/modules/core/mixins/dropdown'

/**
 * This dropdown component will position the items element fixed. This can be useful if
 * the parent element has an `overflow: hidden|scroll`, and you still want the
 * dropdown to break out of it. This property is immutable, so changing it
 * afterwards has no point.
 *
 * The dropdown items don't work in combination with the `moveToBody` because then
 * the `focusin` and `focusout` tab key effect doesn't work anymore. This means
 * that this option will only be compatible with the `app` layout because that one
 * has a max 100% width and height, it won't work in the API docs or publicly shared
 * form for example.
 */
export default {
  name: 'FixedItemsDropdown',
  extends: Dropdown,
  data() {
    return {
      itemsContainerAdditionalClass: 'dropdown__items--fixed',
      selectItemsAdditionalClass: 'select__items--no-max-height',
    }
  },
  beforeDestroy() {
    window.removeEventListener('scroll', this.$el.updatePositionEvent, true)
    window.removeEventListener('resize', this.$el.updatePositionEvent)
  },
  methods: {
    async show(...args) {
      if (this.disabled || this.open) {
        return
      }

      const originalReturnValue = dropdown.methods.show.call(this, ...args)

      const updatePosition = () => {
        const element = this.$refs.itemsContainer
        const targetRect = this.$el.getBoundingClientRect()
        element.style.top = targetRect.top + 'px'
        element.style.left = targetRect.left + 'px'
        element.style['min-width'] = targetRect.width + 'px'
        element.style['max-height'] = `calc(100vh - ${targetRect.top + 20}px)`
      }

      // Delay the position update to the next tick to let the Context content
      // be available in DOM for accurate positioning.
      await this.$nextTick()
      updatePosition()

      this.$el.updatePositionEvent = () => {
        updatePosition()
      }
      window.addEventListener('scroll', this.$el.updatePositionEvent, true)
      window.addEventListener('resize', this.$el.updatePositionEvent)

      return originalReturnValue
    },
    hide(...args) {
      if (this.disabled || !this.open) {
        return
      }

      const originalReturnValue = dropdown.methods.hide.call(this, ...args)

      window.removeEventListener('scroll', this.$el.updatePositionEvent, true)
      window.removeEventListener('resize', this.$el.updatePositionEvent)

      return originalReturnValue
    },
  },
}
</script>
