import { escapeRegExp } from '@baserow/modules/core/utils/string'

export default {
  props: {
    value: {
      validator: () => true,
      required: true,
    },
    name: {
      type: String,
      required: true,
    },
    icon: {
      type: String,
      required: false,
      default: null,
    },
    description: {
      type: String,
      required: false,
      default: null,
    },
    disabled: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  data() {
    return {
      // This field is being used by `getDropdownItemComponents` in ``dropdown.js to
      // figure out if the child component is a dropdown item or not
      isDropdownItem: true,
      query: '',
    }
  },
  methods: {
    select(value, disabled) {
      if (!disabled) {
        this.$parent.select(value)
      }
    },
    hover(value, disabled) {
      if (!disabled && this.$parent.hover !== value) {
        this.$parent.hover = value
      }
    },
    search(query) {
      this.query = query
      return this.isVisible(query)
    },
    isVisible(query) {
      if (!query) {
        return true
      }
      const regex = new RegExp('(' + escapeRegExp(query) + ')', 'i')
      return this.name.match(regex)
    },
    isActive(value) {
      return this.$parent.value === value
    },
    isHovering(value) {
      return this.$parent.hover === value
    },
  },
}
