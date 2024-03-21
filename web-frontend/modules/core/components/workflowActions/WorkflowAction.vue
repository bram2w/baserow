<template>
  <div>
    <div class="workflow-action__header">
      <div
        class="workflow-action__header-handle margin-right-1"
        data-sortable-handle
        @mousedown.prevent
      ></div>
      <WorkflowActionSelector
        :available-workflow-action-types="availableWorkflowActionTypes"
        :workflow-action="workflowAction"
        :disabled="loading"
        @change="updateWorkflowAction({ type: $event })"
        @delete="$emit('delete')"
      />
    </div>
    <component
      :is="workflowActionType.form"
      v-if="workflowActionType.form"
      ref="actionForm"
      :workflow-action="workflowAction"
      :default-values="workflowAction"
      class="margin-top-2"
      @values-changed="updateWorkflowAction($event)"
    ></component>
    <div v-else class="workflow-action__placeholder" />
  </div>
</template>

<script>
import WorkflowActionSelector from '@baserow/modules/core/components/workflowActions/WorkflowActionSelector.vue'
import _ from 'lodash'
import { notifyIf } from '@baserow/modules/core/utils/error'
import { mapActions } from 'vuex'

export default {
  name: 'WorkflowAction',
  components: { WorkflowActionSelector },
  inject: ['page'],
  props: {
    availableWorkflowActionTypes: {
      type: Array,
      required: true,
    },
    workflowAction: {
      type: Object,
      required: false,
      default: null,
    },
  },
  data() {
    return { loading: false }
  },
  computed: {
    workflowActionType() {
      return this.availableWorkflowActionTypes.find(
        (workflowActionType) =>
          workflowActionType.getType() === this.workflowAction.type
      )
    },
  },
  methods: {
    ...mapActions({
      actionUpdateWorkflowAction: 'workflowAction/updateDebounced',
    }),
    async updateWorkflowAction(values) {
      if (this.$refs.actionForm && !this.$refs.actionForm.isFormValid()) {
        return
      }

      // In this case there weren't any actual changes
      if (_.isMatch(this.workflowAction, values)) {
        return
      }
      if (values.type) {
        this.loading = true
      }

      try {
        await this.actionUpdateWorkflowAction({
          page: this.page,
          workflowAction: this.workflowAction,
          values,
        })
      } catch (error) {
        this.$refs.actionForm?.reset()
        notifyIf(error)
      }

      this.loading = false
    },
  },
}
</script>
