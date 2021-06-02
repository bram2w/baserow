<template>
  <Context ref="context">
    <ul class="context__menu">
      <li>
        <a @click="exportView()">
          <i class="context__menu-icon fas fa-fw fa-file-export"></i>
          Export view
        </a>
      </li>
      <li>
        <a @click="enableRename()">
          <i class="context__menu-icon fas fa-fw fa-pen"></i>
          Rename view
        </a>
      </li>
      <li>
        <a @click="deleteView()">
          <i class="context__menu-icon fas fa-fw fa-trash"></i>
          Delete view
        </a>
      </li>
    </ul>
    <DeleteViewModal ref="deleteViewModal" :view="view" />
    <ExportTableModal ref="exportViewModal" :table="table" :view="view" />
  </Context>
</template>

<script>
import context from '@baserow/modules/core/mixins/context'
import ExportTableModal from '@baserow/modules/database/components/export/ExportTableModal'
import DeleteViewModal from './DeleteViewModal'

export default {
  name: 'ViewContext',
  components: { DeleteViewModal, ExportTableModal },
  mixins: [context],
  props: {
    view: {
      type: Object,
      required: true,
    },
    table: {
      type: Object,
      required: true,
    },
  },
  methods: {
    setLoading(view, value) {
      this.$store.dispatch('view/setItemLoading', { view, value })
    },
    enableRename() {
      this.$refs.context.hide()
      this.$emit('enable-rename')
    },
    deleteView() {
      this.$refs.context.hide()
      this.$refs.deleteViewModal.show()
    },
    exportView() {
      this.$refs.context.hide()
      this.$refs.exportViewModal.show()
    },
  },
}
</script>
