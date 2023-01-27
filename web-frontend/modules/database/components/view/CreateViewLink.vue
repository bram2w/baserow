<template>
  <a
    ref="createViewLink"
    v-tooltip="deactivated ? deactivatedText : null"
    class="select__footer-create-link"
    @click="select"
  >
    <i
      class="select__footer-create-icon fas"
      :class="'fa-' + viewType.iconClass"
    ></i>
    {{ viewType.getName() }}
    <div v-if="deactivated" class="deactivated-label">
      <i class="fas fa-lock"></i>
    </div>
    <CreateViewModal
      ref="createModal"
      :table="table"
      :database="database"
      :view-type="viewType"
      @created="$emit('created', $event)"
    ></CreateViewModal>
    <component
      :is="deactivatedClickModal"
      v-if="deactivatedClickModal !== null"
      ref="deactivatedClickModal"
      :name="viewType.getName()"
    ></component>
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
    database: {
      type: Object,
      required: true,
    },
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
      return this.viewType.isDeactivated(this.database.group.id)
    },
    deactivatedClickModal() {
      return this.viewType.getDeactivatedClickModal()
    },
  },
  methods: {
    select() {
      if (!this.deactivated) {
        this.$refs.createModal.show(this.$refs.createViewLink)
      } else if (this.deactivated && this.deactivatedClickModal) {
        this.$refs.deactivatedClickModal.show()
      }
    },
  },
}
</script>
