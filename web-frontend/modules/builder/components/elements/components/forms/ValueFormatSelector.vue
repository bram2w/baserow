<template>
  <TextFormatSelector
    :model-value="format"
    :label="label"
    :horizontal="horizontal"
    @update:model-value="updateFormat"
  />
</template>

<script>
import TextFormatSelector from '@baserow/modules/builder/components/elements/components/forms/TextFormatSelector'
import {
  getFormat,
  getFormulaFormat,
  setFormat,
  setFormulaFormat,
} from '@baserow/modules/core/formula/textFormat'

/**
 * The Plain text / Markdown toggle of a text whose format is stored inside the
 * value itself, as a marker in front of it. The value is either a formula
 * object, in which case the marker goes in front of the formula, or a plain
 * string such as a collection field name.
 */
export default {
  name: 'ValueFormatSelector',
  components: { TextFormatSelector },
  props: {
    modelValue: {
      type: [Object, String],
      required: false,
      default: '',
    },
    label: {
      type: String,
      required: false,
      default: null,
    },
    horizontal: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  emits: ['update:modelValue'],
  computed: {
    isFormula() {
      return typeof this.modelValue === 'object' && this.modelValue !== null
    },
    format() {
      return this.isFormula
        ? getFormulaFormat(this.modelValue)
        : getFormat(this.modelValue)
    },
  },
  methods: {
    updateFormat(format) {
      this.$emit(
        'update:modelValue',
        this.isFormula
          ? setFormulaFormat(this.modelValue, format)
          : setFormat(this.modelValue || '', format)
      )
    },
  },
}
</script>
