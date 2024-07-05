<template>
  <FormGroup
    :label="label"
    :small-label="smallLabel"
    :horizontal="horizontal"
    :helper-text="helpText"
    :required="required"
  >
    <FormulaInputField
      :value="value"
      :placeholder="placeholder"
      :data-providers="dataProviders"
      :data-explorer-loading="dataExplorerLoading"
      :application-context="applicationContext"
      :small="small"
      @input="$emit('input', $event)"
    />
    <template #after-input>
      <slot name="after-input"></slot>
    </template>
  </FormGroup>
</template>

<script>
import FormulaInputField from '@baserow/modules/core/components/formula/FormulaInputField'
export default {
  components: { FormulaInputField },
  props: {
    value: {
      type: String,
      required: true,
    },
    label: {
      type: String,
      required: false,
      default: '',
    },
    placeholder: {
      type: String,
      required: false,
      default: '',
    },
    helpText: {
      type: String,
      required: false,
      default: '',
    },
    small: {
      type: Boolean,
      required: false,
      default: false,
    },
    smallLabel: {
      type: Boolean,
      required: false,
      default: false,
    },
    required: {
      type: Boolean,
      required: false,
      default: false,
    },
    horizontal: {
      type: Boolean,
      required: false,
      default: false,
    },
    dataProviders: {
      type: Array,
      required: false,
      default: () => [],
    },
    dataExplorerLoading: {
      type: Boolean,
      required: false,
      default: false,
    },
    applicationContext: {
      type: Object,
      required: true,
    },
  },
}
</script>
