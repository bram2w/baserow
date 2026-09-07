<template>
  <form @submit.prevent="submit">
    <FormGroup
      small-label
      :label="$t('notificationWorkflowActionForm.titleLabel')"
      class="margin-bottom-2"
      required
    >
      <InjectedFormulaInput
        v-model="values.title"
        :placeholder="$t('notificationWorkflowActionForm.titlePlaceholder')"
      />
    </FormGroup>
    <ValueFormatSelector
      v-model="values.title"
      :label="$t('notificationWorkflowActionForm.titleFormat')"
    />
    <FormGroup
      small-label
      :label="$t('notificationWorkflowActionForm.descriptionLabel')"
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
    <ValueFormatSelector
      v-model="values.description"
      :label="$t('notificationWorkflowActionForm.descriptionFormat')"
    />
  </form>
</template>

<script>
import form from '@baserow/modules/core/mixins/form'
import InjectedFormulaInput from '@baserow/modules/core/components/formula/InjectedFormulaInput'
import ValueFormatSelector from '@baserow/modules/builder/components/elements/components/forms/ValueFormatSelector'

export default {
  name: 'NotificationWorkflowActionForm',
  components: { InjectedFormulaInput, ValueFormatSelector },
  mixins: [form],
  data() {
    return {
      allowedValues: ['title', 'description'],
      values: {
        title: {},
        description: {},
      },
    }
  },
}
</script>
