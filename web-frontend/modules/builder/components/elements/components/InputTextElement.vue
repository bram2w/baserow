<template>
  <ABFormGroup
    :label="resolvedLabel"
    :error-message="errorMessage"
    :autocomplete="isEditMode ? 'off' : ''"
    :required="element.required"
    :style="getStyleOverride('input')"
  >
    <ABInput
      v-model="inputValue"
      :placeholder="resolvedPlaceholder"
      :multiline="element.is_multiline"
      :rows="element.rows"
      :type="element.input_type"
      @blur="onFormElementTouch"
    />
  </ABFormGroup>
</template>

<script>
import formElement from '@baserow/modules/builder/mixins/formElement'
import { ensureString } from '@baserow/modules/core/utils/validator'

export default {
  name: 'InputTextElement',
  mixins: [formElement],
  props: {
    /**
     * @type {Object}
     * @property {string} default_value - The text input's default value.
     * @property {boolean} required - Whether the text input is required.
     * @property {Object} placeholder - The text input's placeholder value.
     * @property {boolean} multiline - Whether the text input is multiline.
     * @property {number} rows - The number of rows (height) of the input.
     */
    element: {
      type: Object,
      required: true,
    },
  },
  computed: {
    resolvedDefaultValue() {
      return ensureString(this.resolveFormula(this.element.default_value))
    },
    resolvedLabel() {
      return ensureString(this.resolveFormula(this.element.label))
    },
    resolvedPlaceholder() {
      return ensureString(this.resolveFormula(this.element.placeholder))
    },
  },
  watch: {
    resolvedDefaultValue: {
      handler(value) {
        this.inputValue = value
      },
      immediate: true,
    },
  },
  methods: {
    getErrorMessage() {
      switch (this.element.validation_type) {
        case 'integer':
          return this.$t('error.invalidNumber')
        case 'email':
          return this.$t('error.invalidEmail')
        default:
          return this.$t('error.requiredField')
      }
    },
  },
}
</script>
