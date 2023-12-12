<template>
  <form @submit.prevent @keydown.enter.prevent>
    <ApplicationBuilderFormulaInputGroup
      v-model="values.submit_button_label"
      :data-providers-allowed="DATA_PROVIDERS_ALLOWED_ELEMENTS"
      :label="$t('formContainerElementForm.submitButtonLabel')"
      :placeholder="$t('formContainerElementForm.submitButtonPlaceholder')"
    />
  </form>
</template>

<script>
import form from '@baserow/modules/core/mixins/form'
import ApplicationBuilderFormulaInputGroup from '@baserow/modules/builder/components/ApplicationBuilderFormulaInputGroup.vue'
import { DATA_PROVIDERS_ALLOWED_ELEMENTS } from '@baserow/modules/builder/enums'

export default {
  name: 'FormContainerElementForm',
  components: { ApplicationBuilderFormulaInputGroup },
  mixins: [form],
  data() {
    return {
      values: {
        submit_button_label: '',
      },
    }
  },
  computed: {
    DATA_PROVIDERS_ALLOWED_ELEMENTS: () => DATA_PROVIDERS_ALLOWED_ELEMENTS,
  },
}
</script>
