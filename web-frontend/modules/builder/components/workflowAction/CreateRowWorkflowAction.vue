<template>
  <UpsertRowWorkflowActionForm
    :workflow-action="workflowAction"
    :default-values="defaultValues.service"
    :application="builder"
    @values-changed="mutateService($event)"
  >
  </UpsertRowWorkflowActionForm>
</template>

<script>
import UpsertRowWorkflowActionForm from '@baserow/modules/integrations/localBaserow/components/services/LocalBaserowUpsertRowServiceForm'
import form from '@baserow/modules/core/mixins/form'
import _ from 'lodash'
import { DATA_PROVIDERS_ALLOWED_ELEMENTS } from '@baserow/modules/builder/enums'

export default {
  name: 'CreateRowWorkflowAction',
  components: { UpsertRowWorkflowActionForm },
  mixins: [form],
  provide() {
    return { dataProvidersAllowed: DATA_PROVIDERS_ALLOWED_ELEMENTS }
  },
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
