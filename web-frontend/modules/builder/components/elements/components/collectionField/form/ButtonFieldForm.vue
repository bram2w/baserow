<template>
  <form @submit.prevent @keydown.enter.prevent>
    <ApplicationBuilderFormulaInputGroup
      v-model="values.label"
      small
      :label="$t('generalForm.labelTitle')"
      :placeholder="$t('buttonFieldForm.labelPlaceholder')"
      :data-providers-allowed="DATA_PROVIDERS_ALLOWED_ELEMENTS"
      :application-context-additions="{
        element,
      }"
      horizontal
    />
    <Alert>
      {{ $t('buttonFieldForm.infoMessage') }}
    </Alert>
  </form>
</template>

<script>
import { DATA_PROVIDERS_ALLOWED_ELEMENTS } from '@baserow/modules/builder/enums'
import form from '@baserow/modules/core/mixins/form'
import ApplicationBuilderFormulaInputGroup from '@baserow/modules/builder/components/ApplicationBuilderFormulaInputGroup'

export default {
  name: 'ButtonFieldForm',
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
      allowedValues: ['label'],
      values: {
        label: '',
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
