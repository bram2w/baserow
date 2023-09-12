import _ from 'lodash'
import form from '@baserow/modules/core/mixins/form'

export default {
  props: {
    element: {
      type: Object,
      required: true,
    },
    parentElement: {
      type: Object,
      required: false,
      default: null,
    },
  },
  mixins: [form],
  data() {
    const allowedValues = this.getAllowedValues()
    return {
      allowedValues,
      values: this.getValuesFromElement(allowedValues),
      boxStyles: Object.fromEntries(
        ['top', 'bottom'].map((pos) => [pos, this.getBoxStyleValue(pos)])
      ),
    }
  },
  watch: {
    boxStyles: {
      deep: true,
      handler(newValue) {
        Object.entries(newValue).forEach(([prop, value]) => {
          this.setBoxStyleValue(prop, value)
        })
      },
    },
  },
  methods: {
    isStyleAllowed(style) {
      return this.allowedValues.includes(style)
    },
    getBoxStyleValue(pos) {
      return { padding: this.defaultValues[`style_padding_${pos}`] }
    },
    setBoxStyleValue(pos, newValue) {
      if (newValue.padding !== undefined) {
        this.values[`style_padding_${pos}`] = newValue.padding
      }
    },
    getAllowedValues() {
      const elementType = this.$registry.get('element', this.element.type)
      const parentElementType = this.parentElement
        ? this.$registry.get('element', this.parentElement?.type)
        : null

      if (!parentElementType) {
        return elementType.styles
      }

      return _.difference(
        elementType.styles,
        parentElementType.childStylesForbidden
      )
    },
    getValuesFromElement(allowedValues) {
      return allowedValues.reduce((obj, value) => {
        obj[value] = this.element[value] || null
        return obj
      }, {})
    },
  },
}
