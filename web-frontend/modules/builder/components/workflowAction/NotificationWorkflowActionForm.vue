<template>
  <form @submit.prevent="submit">
    <FormGroup
      small-label
      :label="$t('notificationWorkflowActionForm.titleLabel')"
      :helper-text="$t('markdownMarker.hint')"
      class="margin-bottom-2"
      required
    >
      <InjectedFormulaInput
        v-model="values.title"
        :placeholder="$t('notificationWorkflowActionForm.titlePlaceholder')"
      />
    </FormGroup>
    <FormGroup
      small-label
      :label="$t('notificationWorkflowActionForm.descriptionLabel')"
      :helper-text="$t('markdownMarker.hint')"
      class="margin-bottom-2"
      required
    >
      <InjectedFormulaInput
        v-model="values.description"
        :placeholder="
          $t('notificationWorkflowActionForm.descriptionPlaceholder')
        "
      />
    </FormGroup>
  </form>
</template>

<script>
import form from '@baserow/modules/core/mixins/form'
import InjectedFormulaInput from '@baserow/modules/core/components/formula/InjectedFormulaInput'

export default {
  name: 'NotificationWorkflowActionForm',
  components: { InjectedFormulaInput },
  mixins: [form],
  data() {
    return {
      values: {
        title: {},
        description: {},
      },
    }
  },
}
</script>
