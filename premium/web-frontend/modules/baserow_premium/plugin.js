import { PremiumPlugin } from '@baserow_premium/plugins'
import {
  JSONTableExporter,
  XMLTableExporter,
} from '@baserow_premium/tableExporterTypes'
import {
  DashboardType,
  GroupsAdminType,
  UsersAdminType,
  LicensesAdminType,
} from '@baserow_premium/adminTypes'
import rowCommentsStore from '@baserow_premium/store/row_comments'
import kanbanStore from '@baserow_premium/store/view/kanban'
import { PremiumDatabaseApplicationType } from '@baserow_premium/applicationTypes'
import { registerRealtimeEvents } from '@baserow_premium/realtime'
import { KanbanViewType } from '@baserow_premium/viewTypes'

import en from '@baserow_premium/locales/en.json'
import fr from '@baserow_premium/locales/fr.json'

export default (context) => {
  const { store, app, isDev } = context

  app.$clientErrorMap.setError(
    'ERROR_NO_ACTIVE_PREMIUM_LICENSE',
    'License required',
    'This functionality requires an active premium license. Please refresh the page.'
  )

  // Allow locale file hot reloading
  if (isDev && app.i18n) {
    const { i18n } = app
    i18n.mergeLocaleMessage('en', en)
    i18n.mergeLocaleMessage('fr', fr)
  }

  store.registerModule('row_comments', rowCommentsStore)
  store.registerModule('page/view/kanban', kanbanStore)
  store.registerModule('template/view/kanban', kanbanStore)

  app.$registry.register('plugin', new PremiumPlugin(context))
  app.$registry.register('admin', new DashboardType(context))
  app.$registry.register('admin', new UsersAdminType(context))
  app.$registry.register('admin', new GroupsAdminType(context))
  app.$registry.register('admin', new LicensesAdminType(context))
  app.$registry.register('exporter', new JSONTableExporter(context))
  app.$registry.register('exporter', new XMLTableExporter(context))
  app.$registry.register('view', new KanbanViewType(context))

  registerRealtimeEvents(app.$realtime)

  // Overwrite the existing database application type with the one customized for
  // premium use.
  app.$registry.register(
    'application',
    new PremiumDatabaseApplicationType(context)
  )
}
