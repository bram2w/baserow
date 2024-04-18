<template>
  <div class="workflow-action-selector">
    <Dropdown
      class="workflow-action-selector__options"
      :value="workflowActionType.getType()"
      :show-search="false"
      :disabled="disabled"
      @change="$emit('change', $event)"
    >
      <DropdownItem
        v-for="availableWorkflowActionType in availableWorkflowActionTypes"
        :key="availableWorkflowActionType.getType()"
        :name="availableWorkflowActionType.label"
        :value="availableWorkflowActionType.getType()"
      ></DropdownItem>
    </Dropdown>
    <div class="margin-left-2">
      <a class="anchor" @click="$emit('delete')">
        <i class="iconoir-bin"></i>
      </a>
    </div>
  </div>
</template>

<script>
export default {
  name: 'WorkflowActionSelector',
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
    disabled: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  computed: {
    workflowActionType() {
      return this.availableWorkflowActionTypes.find(
        (workflowActionType) =>
          workflowActionType.getType() === this.workflowAction.type
      )
    },
  },
}
</script>
