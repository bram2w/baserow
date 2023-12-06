<template>
  <Expandable toggle-on-click>
    <template #header="{ expanded }">
      <div class="event__header">
        <div class="event__header-left">
          <div class="event__label">
            {{ event.label }}
          </div>
          <div
            v-if="workflowActions.length"
            class="margin-left-1 event__amount-actions"
          >
            {{ workflowActions.length }}
          </div>
        </div>
        <a class="event__toggle">
          <i :class="getIcon(expanded)"></i>
        </a>
      </div>
    </template>
    <template #default>
      <div>
        <WorkflowAction
          v-for="(workflowAction, index) in workflowActions"
          :key="workflowAction.id"
          v-sortable="{
            id: workflowAction.id,
            handle: '[data-sortable-handle]',
            update: orderWorkflowActions,
          }"
          class="event__workflow-action"
          :class="{ 'event__workflow-action--first': index === 0 }"
          :available-workflow-action-types="availableWorkflowActionTypes"
          :workflow-action="workflowAction"
          @delete="deleteWorkflowAction(workflowAction)"
        />
      </div>
      <Button
        size="tiny"
        type="link"
        prepend-icon="baserow-icon-plus"
        :loading="addingAction"
        @click="addWorkflowAction"
      >
        {{ $t('event.addAction') }}
      </Button>
    </template>
  </Expandable>
</template>

<script>
import { Event } from '@baserow/modules/builder/eventTypes'
import WorkflowAction from '@baserow/modules/core/components/workflowActions/WorkflowAction.vue'
import { NotificationWorkflowActionType } from '@baserow/modules/builder/workflowActionTypes'
import { mapActions } from 'vuex'
import { notifyIf } from '@baserow/modules/core/utils/error'

const DEFAULT_WORKFLOW_ACTION_TYPE = NotificationWorkflowActionType.getType()

export default {
  name: 'Event',
  components: { WorkflowAction },
  inject: ['page'],
  props: {
    event: {
      type: Event,
      required: true,
    },
    element: {
      type: Object,
      required: true,
    },
    workflowActions: {
      type: Array,
      required: false,
      default: () => [],
    },
    availableWorkflowActionTypes: {
      type: Array,
      required: true,
    },
  },
  data() {
    return {
      addingAction: false,
    }
  },
  methods: {
    ...mapActions({
      actionCreateWorkflowAction: 'workflowAction/create',
      actionDeleteWorkflowAction: 'workflowAction/delete',
      actionOrderWorkflowActions: 'workflowAction/order',
    }),
    getIcon(expanded) {
      return expanded ? 'iconoir-nav-arrow-down' : 'iconoir-nav-arrow-right'
    },
    async addWorkflowAction() {
      this.addingAction = true
      try {
        await this.actionCreateWorkflowAction({
          page: this.page,
          workflowActionType: DEFAULT_WORKFLOW_ACTION_TYPE,
          eventType: this.event.getType(),
          configuration: {
            element_id: this.element.id,
          },
        })
      } catch (error) {
        notifyIf(error)
      }
      this.addingAction = false
    },
    async deleteWorkflowAction(workflowAction) {
      try {
        await this.actionDeleteWorkflowAction({
          page: this.page,
          workflowAction,
        })
      } catch (error) {
        notifyIf(error)
      }
    },
    async orderWorkflowActions(order) {
      try {
        await this.actionOrderWorkflowActions({
          page: this.page,
          element: this.element,
          order,
        })
      } catch (error) {
        notifyIf(error)
      }
    },
  },
}
</script>
