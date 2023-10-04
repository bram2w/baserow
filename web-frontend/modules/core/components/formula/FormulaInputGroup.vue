<template>
  <FormElement class="control" :class="{ 'control--horizontal': horizontal }">
    <label
      v-if="label"
      class="control__label"
      :class="{ 'control__label--small': smallLabel }"
    >
      {{ label }}
    </label>
    <div class="control__elements">
      <FormulaInputField
        :value="value"
        :placeholder="placeholder"
        :data-providers="dataProviders"
        :data-explorer-loading="dataExplorerLoading"
        :application-context="applicationContext"
        @input="$emit('input', $event)"
      />
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
