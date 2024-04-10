<template>
  <UpsertRowWorkflowActionForm
    enable-row-id
    :workflow-action="workflowAction"
    :default-values="defaultValues.service"
    :application="builder"
    @values-changed="mutateService($event)"
  >
  </UpsertRowWorkflowActionForm>
</template>

<script>
import UpsertRowWorkflowActionForm from '@baserow/modules/integrations/localBaserow/components/services/LocalBaserowUpsertRowServiceForm.vue'
import form from '@baserow/modules/core/mixins/form'
import _ from 'lodash'

export default {
  name: 'UpdateRowWorkflowAction',
  components: { UpsertRowWorkflowActionForm },
  mixins: [form],
  inject: ['builder'],
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
  methods: {
    mutateService(newValues) {
      if (!_.isMatch(this.workflowAction.service, newValues)) {
        this.values.service = { ...this.workflowAction.service, ...newValues }
      }
    },
  },
}
</script>
