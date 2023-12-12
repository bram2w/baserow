<template>
  <div>
    <label v-if="element.label" class="control__label">
      {{ resolvedLabelValue }}
    </label>
    <input
      type="text"
      class="input-element"
      :readonly="isEditable"
      :value="resolvedDefaultValue"
      :required="element.required"
      :placeholder="resolvedPlaceholder"
      @input="setFormData($event.target.value)"
    />
  </div>
</template>

<script>
import formElement from '@baserow/modules/builder/mixins/formElement'

export default {
  name: 'InputTextElement',
  mixins: [formElement],
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
    resolvedLabelValue() {
      try {
        return this.resolveFormula(this.element.label)
      } catch (e) {
        return ''
      }
    },
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
  watch: {
    resolvedDefaultValue: {
      handler(value) {
        this.setFormData(value)
      },
      immediate: true,
    },
  },
}
</script>
