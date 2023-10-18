<template>
  <form @submit.prevent="submit">
    <ApplicationBuilderFormulaInputGroup
      v-model="values.url"
      :placeholder="$t('openPageWorkflowActionForm.urlPlaceholder')"
      :data-providers-allowed="dataProvidersAllowed"
      :label="$t('openPageWorkflowActionForm.urlLabel')"
    />
  </form>
</template>

<script>
import workflowActionForm from '@baserow/modules/builder/mixins/workflowActionForm'
import ApplicationBuilderFormulaInputGroup from '@baserow/modules/builder/components/ApplicationBuilderFormulaInputGroup'

export default {
  name: 'OpenPageWorkflowActionForm',
  components: { ApplicationBuilderFormulaInputGroup },
  mixins: [workflowActionForm],
  data() {
    return {
      values: {
        url: '',
      },
    }
  },
}
</script>
