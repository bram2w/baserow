<template>
  <ABButton
    :loading="workflowActionsInProgress"
    @click="fireEvent(elementType.getEventByName(element, eventName))"
  >
    {{ labelWithDefault }}
  </ABButton>
</template>

<script>
import element from '@baserow/modules/builder/mixins/element'

export default {
  name: 'ButtonField',
  mixins: [element],
  props: {
    element: {
      type: Object,
      required: true,
    },
    label: {
      type: String,
      required: true,
    },
    field: {
      type: Object,
      required: true,
    },
  },
  computed: {
    eventName() {
      return `${this.field.uid}_click`
    },
    workflowActionsInProgress() {
      const { recordIndexPath } = this.applicationContext
      const dispatchedById = this.elementType.uniqueElementId(
        this.element,
        recordIndexPath
      )
      const workflowActions = this.$store.getters[
        'workflowAction/getElementWorkflowActions'
      ](this.page, this.element.id)
      return workflowActions
        .filter((wa) => wa.event === this.eventName)
        .some((workflowAction) =>
          this.$store.getters['workflowAction/getDispatching'](
            workflowAction,
            dispatchedById
          )
        )
    },
    labelWithDefault() {
      if (this.label) {
        return this.label
      } else {
        return this.$t('buttonField.noLabel')
      }
    },
  },
}
</script>
