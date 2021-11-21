<template>
  <li class="tree__sub" :class="{ active: table._.selected }">
    <a
      class="tree__sub-link"
      :href="resolveTableHref(database, table)"
      @mousedown.prevent
      @click.prevent="selectTable(database, table)"
    >
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
            {{ $t('sidebarItem.exportTable') }}
          </a>
        </li>
        <li>
          <a @click="openWebhookModal()">
            <i class="context__menu-icon fas fa-fw fa-globe"></i>
            Webhooks
          </a>
        </li>
        <li>
          <a @click="enableRename()">
            <i class="context__menu-icon fas fa-fw fa-pen"></i>
            {{ $t('action.rename') }}
          </a>
        </li>
        <li>
          <a
            :class="{ 'context__menu-item--loading': deleteLoading }"
            @click="deleteTable()"
          >
            <i class="context__menu-icon fas fa-fw fa-trash"></i>
            {{ $t('action.delete') }}
          </a>
        </li>
      </ul>
      <ExportTableModal ref="exportTableModal" :table="table" />
      <WebhookModal ref="webhookModal" :table="table" />
    </Context>
  </li>
</template>

<script>
import { notifyIf } from '@baserow/modules/core/utils/error'
import ExportTableModal from '@baserow/modules/database/components/export/ExportTableModal'
import WebhookModal from '@baserow/modules/database/components/webhook/WebhookModal'

export default {
  name: 'SidebarItem',
  components: { ExportTableModal, WebhookModal },
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
  data() {
    return {
      deleteLoading: false,
    }
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
    exportTable() {
      this.$refs.context.hide()
      this.$refs.exportTableModal.show()
    },
    openWebhookModal() {
      this.$refs.context.hide()
      this.$refs.webhookModal.show()
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
    async deleteTable() {
      this.deleteLoading = true

      try {
        await this.$store.dispatch('table/delete', {
          database: this.database,
          table: this.table,
        })
        await this.$store.dispatch('notification/restore', {
          trash_item_type: 'table',
          trash_item_id: this.table.id,
        })
      } catch (error) {
        notifyIf(error, 'table')
      }

      this.deleteLoading = false
    },
    resolveTableHref(database, table) {
      const props = this.$nuxt.$router.resolve({
        name: 'database-table',
        params: {
          databaseId: database.id,
          tableId: table.id,
        },
      })

      return props.href
    },
  },
}
</script>

<i18n>
{
  "en":{
    "sidebarItem":{
      "exportTable": "Export table"
    }
  },
  "fr":{
    "sidebarItem":{
      "exportTable": "Exporter la table"
    }
  }
}
</i18n>
