<template>
  <form @submit.prevent="submit">
    <ApplicationBuilderFormulaInputGroup
      v-model="values.url"
      small
      small-label
      :placeholder="$t('openPageWorkflowActionForm.urlPlaceholder')"
      :data-providers-allowed="dataProvidersAllowed"
      :label="$t('openPageWorkflowActionForm.urlLabel')"
    />
  </form>
</template>

<script>
import ApplicationBuilderFormulaInputGroup from '@baserow/modules/builder/components/ApplicationBuilderFormulaInputGroup'
import form from '@baserow/modules/core/mixins/form'

export default {
  name: 'OpenPageWorkflowActionForm',
  components: { ApplicationBuilderFormulaInputGroup },
  mixins: [form],
  inject: ['dataProvidersAllowed'],
  data() {
    return {
      values: {
        url: '',
      },
    }
  },
}
</script>
