<template>
  <FormElement
    class="control"
    :class="{ control: !small, 'control--horizontal': horizontal }"
  >
    <label
      v-if="label"
      class="control__label"
      :class="{ 'control__label--small': smallLabel }"
    >
      {{ label }}
    </label>
    <div
      class="control__elements"
      :class="{ 'control__elements--small': small }"
    >
      <FormulaInputField
        :value="value"
        :small="small"
        :placeholder="placeholder"
        :data-providers="dataProviders"
        :data-explorer-loading="dataExplorerLoading"
        :application-context="applicationContext"
        @input="$emit('input', $event)"
      />
      <p v-if="helpText">{{ helpText }}</p>
    </div>
  </FormElement>
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
