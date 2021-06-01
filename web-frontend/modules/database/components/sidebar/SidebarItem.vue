<template>
  <li class="tree__sub" :class="{ active: table._.selected }">
    <a class="tree__sub-link" @click="selectTable(database, table)">
      <Editable
        ref="rename"
        :value="table.name"
        @change="renameTable(database, table, $event)"
      ></Editable>
    </a>
    <a
      v-show="!database._.loading"
      class="tree__options"
      @click="$refs.context.toggle($event.currentTarget, 'bottom', 'right', 0)"
      @mousedown.stop
    >
      <i class="fas fa-ellipsis-v"></i>
    </a>
    <Context ref="context">
      <div class="context__menu-title">{{ table.name }}</div>
      <ul class="context__menu">
        <li>
          <a @click="exportTable()">
            <i class="context__menu-icon fas fa-fw fa-file-export"></i>
            Export table
          </a>
        </li>
        <li>
          <a @click="enableRename()">
            <i class="context__menu-icon fas fa-fw fa-pen"></i>
            Rename
          </a>
        </li>
        <li>
          <a @click="deleteTable()">
            <i class="context__menu-icon fas fa-fw fa-trash"></i>
            Delete
          </a>
        </li>
      </ul>
      <DeleteTableModal
        ref="deleteTableModal"
        :database="database"
        :table="table"
      />
      <ExportTableModal ref="exportTableModal" :table="table" />
    </Context>
  </li>
</template>

<script>
import { notifyIf } from '@baserow/modules/core/utils/error'
import DeleteTableModal from '@baserow/modules/database/components/table/DeleteTableModal'
import ExportTableModal from '@baserow/modules/database/components/export/ExportTableModal'

export default {
  name: 'SidebarItem',
  components: { ExportTableModal, DeleteTableModal },
  props: {
    database: {
      type: Object,
      required: true,
    },
    table: {
      type: Object,
      required: true,
    },
  },
  methods: {
    setLoading(database, value) {
      this.$store.dispatch('application/setItemLoading', {
        application: database,
        value,
      })
    },
    selectTable(database, table) {
      this.setLoading(database, true)

      this.$nuxt.$router.push(
        {
          name: 'database-table',
          params: {
            databaseId: database.id,
            tableId: table.id,
          },
        },
        () => {
          this.setLoading(database, false)
        },
        () => {
          this.setLoading(database, false)
        }
      )
    },
    deleteTable() {
      this.$refs.context.hide()
      this.$refs.deleteTableModal.show()
    },
    exportTable() {
      this.$refs.context.hide()
      this.$refs.exportTableModal.show()
    },
    enableRename() {
      this.$refs.context.hide()
      this.$refs.rename.edit()
    },
    async renameTable(database, table, event) {
      this.setLoading(database, true)

      try {
        await this.$store.dispatch('table/update', {
          database,
          table,
          values: {
            name: event.value,
          },
        })
      } catch (error) {
        this.$refs.rename.set(event.oldValue)
        notifyIf(error, 'table')
      }

      this.setLoading(database, false)
    },
  },
}
</script>
