<template>
  <div>
    <label v-if="element.label" class="control__label">
      {{ resolvedLabel }}
      <span
        v-if="element.label && element.required"
        class="control__label--required"
        :title="$t('error.requiredField')"
        >*</span
      >
    </label>
    <textarea
      v-if="element.is_multiline === true"
      ref="textarea"
      v-model="inputValue"
      class="input-element"
      style="resize: none"
      :required="element.required"
      :placeholder="resolvedPlaceholder"
      :rows="element.rows"
      @blur="onFormElementTouch"
    ></textarea>
    <input
      v-else
      v-model="inputValue"
      type="text"
      class="input-element"
      :class="{
        'input-element--error': displayFormDataError,
      }"
      :required="element.required"
      :placeholder="resolvedPlaceholder"
      @blur="onFormElementTouch"
    />
    <div v-if="displayFormDataError" class="error">
      <i class="iconoir-warning-triangle"></i>
      {{ errorForValidationType }}
    </div>
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
    resolvedDefaultValue() {
      return this.resolveFormula(this.element.default_value)
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
    async 'element.rows'(value) {
      await this.$nextTick()
      this.updateTextareaHeight()
    },
    async 'element.is_multiline'(value) {
      await this.$nextTick()
      this.updateTextareaHeight()
    },
    inputValue: {
      async handler() {
        await this.$nextTick()
        this.updateTextareaHeight()
      },
      immediate: true,
    },
  },
  mounted() {
    this.updateTextareaHeight()
  },
  methods: {
    updateTextareaHeight() {
      if (this.element.is_multiline && this.$refs.textarea) {
        const textarea = this.$refs.textarea
        textarea.style.height = 'auto'
        textarea.style.height = `${textarea.scrollHeight + 2}px`
      }
    },
  },
}
</script>
