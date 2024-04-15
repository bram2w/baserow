<template>
  <form @submit.prevent @keydown.enter.prevent>
    <ApplicationBuilderFormulaInputGroup
      v-model="values.value"
      :label="$t('textFieldForm.fieldValueLabel')"
      :placeholder="$t('textFieldForm.fieldValuePlaceholder')"
      :data-providers-allowed="DATA_PROVIDERS_ALLOWED_ELEMENTS"
      :application-context-additions="{
        element,
      }"
      horizontal
    />
  </form>
</template>

<script>
import { DATA_PROVIDERS_ALLOWED_ELEMENTS } from '@baserow/modules/builder/enums'
import form from '@baserow/modules/core/mixins/form'
import ApplicationBuilderFormulaInputGroup from '@baserow/modules/builder/components/ApplicationBuilderFormulaInputGroup'

export default {
  name: 'BooleanFieldForm',
  components: { ApplicationBuilderFormulaInputGroup },
  mixins: [form],
  props: {
    element: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      allowedValues: ['value'],
      values: {
        value: '',
      },
    }
  },
  computed: {
    DATA_PROVIDERS_ALLOWED_ELEMENTS() {
      return DATA_PROVIDERS_ALLOWED_ELEMENTS
    },
  },
}
</script>
