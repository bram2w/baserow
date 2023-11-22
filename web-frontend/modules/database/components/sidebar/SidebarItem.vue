<template>
  <li class="tree__sub" :class="{ active: table._.selected }">
    <a
      class="tree__sub-link"
      :title="table.name"
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
      v-if="showOptions"
      v-show="!database._.loading"
      class="tree__options"
      @click="$refs.context.toggle($event.currentTarget, 'bottom', 'right', 0)"
      @mousedown.stop
    >
      <i class="baserow-icon-more-vertical"></i>
    </a>

    <Context
      ref="context"
      :overflow-scroll="true"
      :max-height-if-outside-viewport="true"
    >
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
      <WebhookModal ref="webhookModal" :table="table" />
    </Context>
  </li>
</template>

<script>
import VueRouter from 'vue-router'
import { notifyIf } from '@baserow/modules/core/utils/error'
import ExportTableModal from '@baserow/modules/database/components/export/ExportTableModal'
import WebhookModal from '@baserow/modules/database/components/webhook/WebhookModal'
import SidebarDuplicateTableContextItem from '@baserow/modules/database/components/sidebar/table/SidebarDuplicateTableContextItem'

export default {
  name: 'SidebarItem',
  components: {
    ExportTableModal,
    WebhookModal,
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
      } catch (error) {
        // When redirecting to the `database-table`, it can happen that it redirects
        // to another view. For some reason, this is causing the router throw an
        // error. In our case, it's perfectly fine, so we're suppressing this error
        // here. More information:
        // https://stackoverflow.com/questions/62223195/vue-router-uncaught-in-promise-
        // error-redirected-from-login-to-via-a
        const { isNavigationFailure, NavigationFailureType } = VueRouter
        if (!isNavigationFailure(error, NavigationFailureType.redirected)) {
          throw error
        }
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
