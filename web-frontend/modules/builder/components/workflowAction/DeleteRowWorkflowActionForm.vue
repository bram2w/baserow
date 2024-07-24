<template>
  <form @submit.prevent>
    <LocalBaserowServiceForm
      enable-row-id
      :default-values="defaultValues.service"
      @values-changed="
        values.service = { ...workflowAction.service, ...$event }
      "
    ></LocalBaserowServiceForm>
  </form>
</template>

<script>
import form from '@baserow/modules/core/mixins/form'
import LocalBaserowServiceForm from '@baserow/modules/integrations/localBaserow/components/services/LocalBaserowServiceForm'

export default {
  name: 'DeleteRowWorkflowActionForm',
  components: {
    LocalBaserowServiceForm,
  },
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
}
</script>
