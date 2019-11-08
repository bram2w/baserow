<template>
  <li class="tree-sub" :class="{ active: table._.selected }">
    <nuxt-link
      :to="{
        name: 'database-table',
        params: {
          id: database.id,
          tableId: table.id
        }
      }"
      class="tree-sub-link"
    >
      <Editable
        ref="rename"
        :value="table.name"
        @change="renameTable(database, table, $event)"
      ></Editable>
    </nuxt-link>
    <a
      v-show="!database._.loading"
      class="tree-options"
      @click="$refs.context.toggle($event.currentTarget, 'bottom', 'right', 0)"
    >
      <i class="fas fa-ellipsis-v"></i>
    </a>
    <Context ref="context">
      <div class="context-menu-title">{{ table.name }}</div>
      <ul class="context-menu">
        <li>
          <a @click="enableRename()">
            <i class="context-menu-icon fas fa-fw fa-pen"></i>
            Rename
          </a>
        </li>
        <li>
          <a @click="deleteTable(database, table)">
            <i class="context-menu-icon fas fa-fw fa-trash"></i>
            Delete
          </a>
        </li>
      </ul>
    </Context>
  </li>
</template>

<script>
import { notifyIf } from '@/utils/error'

export default {
  name: 'SidebarItem',
  props: {
    database: {
      type: Object,
      required: true
    },
    table: {
      type: Object,
      required: true
    }
  },
  methods: {
    setLoading(database, value) {
      this.$store.dispatch('application/setItemLoading', {
        application: database,
        value
      })
    },
    deleteTable(database, table) {
      this.$refs.context.hide()
      this.setLoading(database, true)

      this.$store
        .dispatch('table/delete', { database, table })
        .catch(error => {
          notifyIf(error, 'table')
        })
        .then(() => {
          this.setLoading(database, false)
        })
    },
    enableRename() {
      this.$refs.context.hide()
      this.$refs.rename.edit()
    },
    renameTable(database, table, event) {
      this.setLoading(database, true)

      this.$store
        .dispatch('table/update', {
          database,
          table,
          values: {
            name: event.value
          }
        })
        .catch(error => {
          this.$refs.rename.set(event.oldValue)
          notifyIf(error, 'table')
        })
        .then(() => {
          this.setLoading(database, false)
        })
    }
  }
}
</script>
