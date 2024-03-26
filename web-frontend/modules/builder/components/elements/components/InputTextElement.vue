<template>
  <div>
    <ABFormGroup
      :label="resolvedLabel"
      :is-in-error="displayFormDataError"
      :error-message="errorForValidationType"
      :autocomplete="isEditMode ? 'off' : ''"
      :required="element.required"
    >
      <ABInput
        v-model="inputValue"
        :placeholder="resolvedPlaceholder"
        :multiline="element.is_multiline"
        :rows="element.rows"
        @blur="onFormElementTouch"
      />
    </ABFormGroup>
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
     * @property {boolean} multiline - Whether the text input is multiline.
     * @property {number} rows - The number of rows (height) of the input.
     */
    element: {
      type: Object,
      required: true,
    },
  },
  computed: {
    errorForValidationType() {
      switch (this.element.validation_type) {
        case 'integer':
          return this.$t('error.invalidNumber')
        case 'email':
          return this.$t('error.invalidEmail')
        default:
          return this.$t('error.requiredField')
      }
    },
    resolvedLabel() {
      return this.resolveFormula(this.element.label)
    },
    resolvedPlaceholder() {
      return this.resolveFormula(this.element.placeholder)
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
}
</script>
