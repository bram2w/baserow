<template>
  <form @submit.prevent="submit">
    <ApplicationBuilderFormulaInputGroup
      v-model="values.title"
      small
      small-label
      :placeholder="$t('notificationWorkflowActionForm.titlePlaceholder')"
      :data-providers-allowed="dataProvidersAllowed"
      :label="$t('notificationWorkflowActionForm.titleLabel')"
    />
    <ApplicationBuilderFormulaInputGroup
      v-model="values.description"
      small
      small-label
      :placeholder="$t('notificationWorkflowActionForm.descriptionPlaceholder')"
      :data-providers-allowed="dataProvidersAllowed"
      :label="$t('notificationWorkflowActionForm.descriptionLabel')"
    />
  </form>
</template>

<script>
import ApplicationBuilderFormulaInputGroup from '@baserow/modules/builder/components/ApplicationBuilderFormulaInputGroup.vue'
import form from '@baserow/modules/core/mixins/form'

export default {
  name: 'NotificationWorkflowActionForm',
  components: { ApplicationBuilderFormulaInputGroup },
  mixins: [form],
  inject: ['dataProvidersAllowed'],
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
