<template>
  <form @submit.prevent="submit">
    <InjectedFormulaInputGroup
      v-model="values.title"
      small
      small-label
      :placeholder="$t('notificationWorkflowActionForm.titlePlaceholder')"
      :label="$t('notificationWorkflowActionForm.titleLabel')"
    />
    <InjectedFormulaInputGroup
      v-model="values.description"
      small
      small-label
      :placeholder="$t('notificationWorkflowActionForm.descriptionPlaceholder')"
      :label="$t('notificationWorkflowActionForm.descriptionLabel')"
    />
  </form>
</template>

<script>
import form from '@baserow/modules/core/mixins/form'
import InjectedFormulaInputGroup from '@baserow/modules/core/components/formula/InjectedFormulaInputGroup'

export default {
  name: 'NotificationWorkflowActionForm',
  components: { InjectedFormulaInputGroup },
  mixins: [form],
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
