<template>
  <input
    type="text"
    class="input-element"
    :readonly="isEditable"
    :value="resolvedDefaultValue"
    :required="element.required"
    :placeholder="resolvedPlaceholder"
  />
</template>

<script>
import element from '@baserow/modules/builder/mixins/element'

export default {
  name: 'InputTextElement',
  mixins: [element],
  props: {
    /**
     * @type {Object}
     * @property {string} default_value - The text input's default value.
     * @property {boolean} required - Whether the text input is required.
     * @property {Object} placeholder - The text input's placeholder value.
     */
    element: {
      type: Object,
      required: true,
    },
  },
  computed: {
    resolvedDefaultValue() {
      try {
        return this.resolveFormula(this.element.default_value)
      } catch (e) {
        return ''
      }
    },
    resolvedPlaceholder() {
      try {
        return this.resolveFormula(this.element.placeholder)
      } catch (e) {
        return ''
      }
    },
  },
}
</script>
