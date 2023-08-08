import _ from 'lodash'

export default {
  props: {
    element: {
      type: Object,
      required: true,
    },
    mode: {
      type: String,
      required: false,
      default: '',
    },
  },
  computed: {
    component() {
      const elementType = this.$registry.get('element', this.element.type)
      const componentName =
        this.mode === 'editing' ? 'editComponent' : 'component'
      return elementType[componentName]
    },
    children() {
      return this.$store.getters['element/getChildren'](this.element)
    },
    allowedStyles() {
      const parentElement = this.$store.getters['element/getElementById'](
        this.element.parent_element_id
      )

      const elementType = this.$registry.get('element', this.element.type)
      const parentElementType = this.parentElement
        ? this.$registry.get('element', parentElement?.type)
        : null

      return !parentElementType
        ? elementType.styles
        : _.difference(
            elementType.styles,
            parentElementType.childStylesForbidden
          )
    },
    baseStyles() {
      const stylesAllowed = this.allowedStyles

      const styles = {
        style_padding_top: {
          'padding-top': `${this.element.style_padding_top || 0}px`,
        },
        style_padding_bottom: {
          'padding-bottom': `${this.element.style_padding_bottom || 0}px`,
        },
      }

      return Object.keys(styles).reduce((acc, key) => {
        if (stylesAllowed.includes(key)) {
          acc = { ...acc, ...styles[key] }
        }
        return acc
      }, {})
    },
  },
}
