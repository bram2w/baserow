<template>
  <UpsertRowWorkflowActionForm
    :workflow-action="workflowAction"
    :default-values="defaultValues.service"
    @values-changed="values.service = { ...workflowAction.service, ...$event }"
  >
  </UpsertRowWorkflowActionForm>
</template>

<script>
import UpsertRowWorkflowActionForm from '@baserow/modules/integrations/localBaserow/components/services/LocalBaserowUpsertRowServiceForm'
import form from '@baserow/modules/core/mixins/form'

export default {
  name: 'CreateRowWorkflowAction',
  components: { UpsertRowWorkflowActionForm },
  mixins: [form],
  props: {
    workflowAction: {
      type: Object,
      required: false,
      default: null,
    },
  },
  data() {
    return {
      allowedValues: ['service'],
      values: {
        service: {},
      },
    }
  },
}
</script>
