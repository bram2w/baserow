<template>
  <Modal class="select-row-modal" @hidden="$emit('hidden')">
    <!--
    Because of how the moveToBody mixin works it takes a small moment before the $refs
    become available. In order for the Scrollbars components to work the refs need to
    be available right away. That is the reason why the contents of the SelectRowModal
    have been moved to a separate component.
    -->
    <SelectRowContent
      :table-id="tableId"
      :value="value"
      @selected="selected"
    ></SelectRowContent>
  </Modal>
</template>

<script>
import modal from '@baserow/modules/core/mixins/modal'

import SelectRowContent from './SelectRowContent'

export default {
  name: 'SelectRowModal',
  components: { SelectRowContent },
  mixins: [modal],
  props: {
    tableId: {
      type: Number,
      required: true,
    },
    value: {
      type: Array,
      required: false,
      default: () => [],
    },
  },
  methods: {
    /**
     * Hide the modal when a row has been selected.
     */
    selected(...args) {
      this.hide()
      this.$emit('selected', ...args)
    },
  },
}
</script>
