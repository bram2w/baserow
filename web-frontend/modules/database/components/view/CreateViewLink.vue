<template>
  <a
    ref="createViewLink"
    v-tooltip="deactivated ? deactivatedText : null"
    class="select__footer-create-link"
    :class="{
      'select__footer-create-link--disabled': deactivated,
    }"
    @click="!deactivated && $refs.createModal.show($refs.createViewLink)"
  >
    <i
      class="select__footer-create-icon fas"
      :class="'fa-' + viewType.iconClass"
    ></i>
    {{ viewType.getName() }}
    <CreateViewModal
      ref="createModal"
      :table="table"
      :view-type="viewType"
      @created="$emit('created', $event)"
    ></CreateViewModal>
  </a>
</template>

<script>
import CreateViewModal from '@baserow/modules/database/components/view/CreateViewModal'

export default {
  name: 'ViewsContext',
  components: {
    CreateViewModal,
  },
  props: {
    table: {
      type: Object,
      required: true,
    },
    viewType: {
      type: Object,
      required: true,
    },
  },
  computed: {
    deactivatedText() {
      return this.viewType.getDeactivatedText()
    },
    deactivated() {
      return this.viewType.isDeactivated()
    },
  },
}
</script>
