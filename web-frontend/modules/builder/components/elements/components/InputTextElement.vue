<template>
  <div>
    <label v-if="element.label" class="control__label">
      {{ resolvedLabel }}
    </label>
    <input
      type="text"
      class="input-element"
      :readonly="isEditMode"
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
    resolvedLabel() {
      return this.resolveFormula(this.element.label)
    },
    resolvedDefaultValue() {
      return this.resolveFormula(this.element.default_value)
    },
    resolvedPlaceholder() {
      return this.resolveFormula(this.element.placeholder)
    },
  },
  watch: {
    'element.default_value'(value) {
      this.setFormData(this.resolveFormula(value))
    },
  },
}
</script>
