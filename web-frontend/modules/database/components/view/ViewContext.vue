<template>
  <Context ref="context">
    <div class="context__menu-title">{{ view.name }} ({{ view.id }})</div>
    <ul class="context__menu">
      <li
        v-if="
          hasValidExporter &&
          $hasPermission('database.table.run_export', table, database.group.id)
        "
      >
        <a @click="exportView()">
          <i class="context__menu-icon fas fa-fw fa-file-export"></i>
          {{ $t('viewContext.exportView') }}
        </a>
      </li>
      <li
        v-if="
          $hasPermission('database.table.import_rows', table, database.group.id)
        "
      >
        <a @click="importFile()">
          <i class="context__menu-icon fas fa-fw fa-file-import"></i>
          {{ $t('viewContext.importFile') }}
        </a>
      </li>
      <li
        v-if="
          $hasPermission(
            'database.table.view.duplicate',
            table,
            database.group.id
          )
        "
      >
        <a @click="duplicateView()">
          <i class="context__menu-icon fas fa-fw fa-clone"></i>
          {{ $t('viewContext.duplicateView') }}
        </a>
      </li>
      <li
        v-if="
          $hasPermission(
            'database.table.create_webhook',
            table,
            database.group.id
          )
        "
      >
        <a @click="openWebhookModal()">
          <i class="context__menu-icon fas fa-fw fa-globe"></i>
          {{ $t('viewContext.webhooks') }}
        </a>
      </li>
      <li
        v-if="
          $hasPermission('database.table.view.update', view, database.group.id)
        "
      >
        <a @click="enableRename()">
          <i class="context__menu-icon fas fa-fw fa-pen"></i>
          {{ $t('viewContext.renameView') }}
        </a>
      </li>
      <li
        v-if="
          $hasPermission('database.table.view.delete', view, database.group.id)
        "
      >
        <a @click="deleteView()">
          <i class="context__menu-icon fas fa-fw fa-trash"></i>
          {{ $t('viewContext.deleteView') }}
        </a>
      </li>
    </ul>
    <ExportTableModal
      ref="exportViewModal"
      :database="database"
      :table="table"
      :view="view"
    />
    <ImportFileModal
      ref="importFileModal"
      :database="database"
      :table="table"
      :fields="fields"
    />
    <WebhookModal ref="webhookModal" :table="table" />
  </Context>
</template>

<script>
import { mapGetters } from 'vuex'
import context from '@baserow/modules/core/mixins/context'
import error from '@baserow/modules/core/mixins/error'
import viewTypeHasExporterTypes from '@baserow/modules/database/utils/viewTypeHasExporterTypes'
import ImportFileModal from '@baserow/modules/database/components/table/ImportFileModal'

import ExportTableModal from '@baserow/modules/database/components/export/ExportTableModal'
import WebhookModal from '@baserow/modules/database/components/webhook/WebhookModal.vue'

export default {
  name: 'ViewContext',
  components: { ExportTableModal, WebhookModal, ImportFileModal },
  mixins: [context, error],
  props: {
    database: {
      type: Object,
      required: true,
    },
    view: {
      type: Object,
      required: true,
    },
    table: {
      type: Object,
      required: true,
    },
  },
  computed: {
    hasValidExporter() {
      return viewTypeHasExporterTypes(this.view.type, this.$registry)
    },
    ...mapGetters({
      fields: 'field/getAll',
    }),
  },
  methods: {
    setLoading(view, value) {
      this.$store.dispatch('view/setItemLoading', { view, value })
    },
    enableRename() {
      this.$refs.context.hide()
      this.$emit('enable-rename')
    },
    async deleteView() {
      this.setLoading(this.view, true)

      try {
        await this.$store.dispatch('view/delete', this.view)
      } catch (error) {
        this.handleError(error, 'view')
      }

      this.setLoading(this.view, false)
    },
    async duplicateView() {
      this.setLoading(this.view, true)
      let newView

      try {
        newView = await this.$store.dispatch('view/duplicate', this.view)
      } catch (error) {
        this.handleError(error, 'view')
      }

      this.$refs.context.hide()
      this.setLoading(this.view, false)

      // Redirect to the newly created view.
      this.$nuxt.$router.push({
        name: 'database-table',
        params: {
          databaseId: this.table.database_id,
          tableId: this.table.id,
          viewId: newView.id,
        },
      })
    },
    exportView() {
      this.$refs.context.hide()
      this.$refs.exportViewModal.show()
    },
    importFile() {
      this.$refs.context.hide()
      this.$refs.importFileModal.show()
    },
    openWebhookModal() {
      this.$refs.context.hide()
      this.$refs.webhookModal.show()
    },
  },
}
</script>
