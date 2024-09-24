<template>
  <li class="tree__sub" :class="{ active: table._.selected }">
    <a
      class="tree__sub-link"
      :class="{ 'tree__sub-link--empty': table.name === '' }"
      :title="table.name"
      :href="resolveTableHref(database, table)"
      @mousedown.prevent
      @click.prevent="selectTable(database, table)"
    >
      <i
        v-if="table.data_sync"
        v-tooltip:[syncTooltipOptions]="
          `${$t('sidebarItem.lastSynced')}: ${lastSyncedDate}`
        "
        class="iconoir-data-transfer-down"
      ></i>
      <Editable
        ref="rename"
        :value="table.name"
        @change="renameTable(database, table, $event)"
      ></Editable>
    </a>

    <a
      v-if="showOptions"
      v-show="!database._.loading"
      class="tree__options"
      @click="$refs.context.toggle($event.currentTarget, 'bottom', 'right', 0)"
      @mousedown.stop
    >
      <i class="baserow-icon-more-vertical"></i>
    </a>

    <Context ref="context" overflow-scroll max-height-if-outside-viewport>
      <div class="context__menu-title">{{ table.name }} ({{ table.id }})</div>
      <ul class="context__menu">
        <li
          v-for="(component, index) in additionalContextComponents"
          :key="index"
          class="context__menu-item"
          @click="$refs.context.hide()"
        >
          <component
            :is="component"
            :table="table"
            :database="database"
          ></component>
        </li>
        <li
          v-if="
            $hasPermission(
              'database.table.run_export',
              table,
              database.workspace.id
            )
          "
          class="context__menu-item"
        >
          <a class="context__menu-item-link" @click="exportTable()">
            <i class="context__menu-item-icon iconoir-share-ios"></i>
            {{ $t('sidebarItem.exportTable') }}
          </a>
        </li>
        <li
          v-if="
            $hasPermission(
              'database.table.create_webhook',
              table,
              database.workspace.id
            )
          "
          class="context__menu-item"
        >
          <a class="context__menu-item-link" @click="openWebhookModal()">
            <i class="context__menu-item-icon iconoir-globe"></i>
            {{ $t('sidebarItem.webhooks') }}
          </a>
        </li>
        <li
          v-if="
            $hasPermission(
              'database.data_sync.sync_table',
              table,
              database.workspace.id
            )
          "
          class="context__menu-item"
        >
          <a class="context__menu-item-link" @click="openSyncModal()">
            <i class="context__menu-item-icon iconoir-data-transfer-down"></i>
            {{ $t('sidebarItem.sync') }}
          </a>
        </li>
        <li
          v-if="
            $hasPermission(
              'database.table.update',
              table,
              database.workspace.id
            )
          "
          class="context__menu-item"
        >
          <a class="context__menu-item-link" @click="enableRename()">
            <i class="context__menu-item-icon iconoir-edit-pencil"></i>
            {{ $t('action.rename') }}
          </a>
        </li>
        <li
          v-if="
            $hasPermission(
              'database.table.duplicate',
              table,
              database.workspace.id
            )
          "
          class="context__menu-item"
        >
          <SidebarDuplicateTableContextItem
            :database="database"
            :table="table"
            :disabled="deleteLoading"
            @click="$refs.context.hide()"
          ></SidebarDuplicateTableContextItem>
        </li>
        <li
          v-if="
            $hasPermission(
              'database.table.delete',
              table,
              database.workspace.id
            )
          "
          class="context__menu-item"
        >
          <a
            class="context__menu-item-link context__menu-item-link--delete"
            :class="{ 'context__menu-item-link--loading': deleteLoading }"
            @click="deleteTable()"
          >
            <i class="context__menu-item-icon iconoir-bin"></i>
            {{ $t('action.delete') }}
          </a>
        </li>
      </ul>
      <ExportTableModal
        ref="exportTableModal"
        :database="database"
        :table="table"
      />
      <WebhookModal ref="webhookModal" :database="database" :table="table" />
      <SyncTableModal ref="syncModal" :table="table"></SyncTableModal>
    </Context>
  </li>
</template>

<script>
import { notifyIf } from '@baserow/modules/core/utils/error'
import { getHumanPeriodAgoCount } from '@baserow/modules/core/utils/date'
import ExportTableModal from '@baserow/modules/database/components/export/ExportTableModal'
import WebhookModal from '@baserow/modules/database/components/webhook/WebhookModal'
import SidebarDuplicateTableContextItem from '@baserow/modules/database/components/sidebar/table/SidebarDuplicateTableContextItem'
import SyncTableModal from '@baserow/modules/database/components/dataSync/SyncTableModal'

export default {
  name: 'SidebarItem',
  components: {
    ExportTableModal,
    WebhookModal,
    SyncTableModal,
    SidebarDuplicateTableContextItem,
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
  },
  data() {
    return {
      deleteLoading: false,
    }
  },
  computed: {
    showOptions() {
      return (
        this.$hasPermission(
          'database.table.run_export',
          this.table,
          this.database.workspace.id
        ) ||
        this.$hasPermission(
          'database.table.create_webhook',
          this.table,
          this.database.workspace.id
        ) ||
        this.$hasPermission(
          'database.table.update',
          this.table,
          this.database.workspace.id
        ) ||
        this.$hasPermission(
          'database.table.duplicate',
          this.table,
          this.database.workspace.id
        )
      )
    },
    additionalContextComponents() {
      return Object.values(this.$registry.getAll('plugin'))
        .reduce(
          (components, plugin) =>
            components.concat(
              plugin.getAdditionalTableContextComponents(
                this.database.workspace,
                this.table
              )
            ),
          []
        )
        .filter((component) => component !== null)
    },
    syncTooltipOptions() {
      return {
        contentClasses: ['tooltip__content--align-right'],
      }
    },
    lastSyncedDate() {
      if (!this.table.data_sync || !this.table.data_sync.last_sync) {
        return this.$t('sidebarItem.notSynced')
      }
      const { period, count } = getHumanPeriodAgoCount(
        this.table.data_sync.last_sync
      )
      return this.$tc(`datetime.${period}Ago`, count)
    },
  },
  methods: {
    setLoading(database, value) {
      this.$store.dispatch('application/setItemLoading', {
        application: database,
        value,
      })
    },
    async selectTable(database, table) {
      this.setLoading(database, true)

      try {
        await this.$nuxt.$router.push({
          name: 'database-table',
          params: {
            databaseId: database.id,
            tableId: table.id,
          },
        })
      } finally {
        this.setLoading(database, false)
      }
    },
    exportTable() {
      this.$refs.context.hide()
      this.$refs.exportTableModal.show()
    },
    openWebhookModal() {
      this.$refs.context.hide()
      this.$refs.webhookModal.show()
    },
    openSyncModal() {
      this.$refs.context.hide()
      this.$refs.syncModal.show()
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
        await this.$store.dispatch('toast/restore', {
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
