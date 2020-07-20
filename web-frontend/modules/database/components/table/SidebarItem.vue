<template>
  <li class="tree__sub" :class="{ active: table._.selected }">
    <nuxt-link
      :to="{
        name: 'database-table',
        params: {
          databaseId: database.id,
          tableId: table.id,
        },
      }"
      class="tree__sub-link"
    >
      <Editable
        ref="rename"
        :value="table.name"
        @change="renameTable(database, table, $event)"
      ></Editable>
    </nuxt-link>
    <a
      v-show="!database._.loading"
      class="tree__options"
      @click="$refs.context.toggle($event.currentTarget, 'bottom', 'right', 0)"
    >
      <i class="fas fa-ellipsis-v"></i>
    </a>
    <Context ref="context">
      <div class="context__menu-title">{{ table.name }}</div>
      <ul class="context__menu">
        <li>
          <a @click="enableRename()">
            <i class="context__menu-icon fas fa-fw fa-pen"></i>
            Rename
          </a>
        </li>
        <li>
          <a @click="deleteTable(database, table)">
            <i class="context__menu-icon fas fa-fw fa-trash"></i>
            Delete
          </a>
        </li>
      </ul>
    </Context>
  </li>
</template>

<script>
import { notifyIf } from '@baserow/modules/core/utils/error'

export default {
  name: 'SidebarItem',
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
    async deleteTable(database, table) {
      this.$refs.context.hide()
      this.setLoading(database, true)

      try {
        await this.$store.dispatch('table/delete', { database, table })
      } catch (error) {
        notifyIf(error, 'table')
      }

      this.setLoading(database, false)
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
