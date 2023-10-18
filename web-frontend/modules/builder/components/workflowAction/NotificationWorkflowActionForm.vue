<template>
  <form @submit.prevent="submit">
    <ApplicationBuilderFormulaInputGroup
      v-model="values.title"
      :placeholder="$t('notificationWorkflowActionForm.titlePlaceholder')"
      :data-providers-allowed="dataProvidersAllowed"
      :label="$t('notificationWorkflowActionForm.titleLabel')"
    />
    <ApplicationBuilderFormulaInputGroup
      v-model="values.description"
      :placeholder="$t('notificationWorkflowActionForm.descriptionPlaceholder')"
      :data-providers-allowed="dataProvidersAllowed"
      :label="$t('notificationWorkflowActionForm.descriptionLabel')"
    />
  </form>
</template>

<script>
import workflowActionForm from '@baserow/modules/builder/mixins/workflowActionForm'
import ApplicationBuilderFormulaInputGroup from '@baserow/modules/builder/components/ApplicationBuilderFormulaInputGroup.vue'

export default {
  name: 'NotificationWorkflowActionForm',
  components: { ApplicationBuilderFormulaInputGroup },
  mixins: [workflowActionForm],
  data() {
    return {
      values: {
        title: '',
        description: '',
      },
    }
  },
}
</script>
