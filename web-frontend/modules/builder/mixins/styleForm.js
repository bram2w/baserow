import _ from 'lodash'
import form from '@baserow/modules/core/mixins/form'
import { resolveColor } from '@baserow/modules/core/utils/colors'
import { themeToColorVariables } from '@baserow/modules/builder/utils/theme'

export default {
  inject: ['builder'],
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
  computed: {
    colorVariables() {
      return themeToColorVariables(this.builder.theme)
    },
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
    resolveColor,
    isStyleAllowed(style) {
      return this.allowedValues.includes(style)
    },
    getBoxStyleValue(pos) {
      return {
        padding: this.defaultValues[`style_padding_${pos}`],
        border_color: this.defaultValues[`style_border_${pos}_color`],
        border_size: this.defaultValues[`style_border_${pos}_size`],
      }
    },
    setBoxStyleValue(pos, newValue) {
      if (newValue.padding !== undefined) {
        this.values[`style_padding_${pos}`] = newValue.padding
        this.values[`style_border_${pos}_color`] = newValue.border_color
        this.values[`style_border_${pos}_size`] = newValue.border_size
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
