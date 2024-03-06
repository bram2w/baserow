<template>
  <div>
    <label v-if="element.label" class="control__label">
      {{ resolvedLabel }}
    </label>
    <textarea
      v-if="element.is_multiline === true"
      ref="textarea"
      class="input-element"
      style="resize: none"
      :value="resolvedDefaultValue"
      :required="element.required"
      :placeholder="resolvedPlaceholder"
      :rows="element.rows"
      @input="
        setFormData($event.target.value)
        updateTextareaHeight()
      "
    ></textarea>
    <input
      v-else
      type="text"
      class="input-element"
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
     * @property {boolean} multiline - Whether the text input is multiline.
     * @property {number} rows - The number of rows (height) of the input.
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
    async 'element.default_value'(value) {
      this.setFormData(this.resolveFormula(value))
      await this.$nextTick()
      this.updateTextareaHeight()
    },
    async 'element.rows'(value) {
      await this.$nextTick()
      this.updateTextareaHeight()
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
