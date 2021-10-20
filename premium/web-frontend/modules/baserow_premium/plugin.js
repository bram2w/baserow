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
import { PremiumDatabaseApplicationType } from '@baserow_premium/applicationTypes'
import { registerRealtimeEvents } from '@baserow_premium/realtime'

export default (context) => {
  const { store, app } = context

  app.$clientErrorMap.setError(
    'ERROR_NO_ACTIVE_PREMIUM_LICENSE',
    'License required',
    'This functionality requires an active premium license. Please refresh the page.'
  )

  store.registerModule('row_comments', rowCommentsStore)

  app.$registry.register('plugin', new PremiumPlugin(context))
  app.$registry.register('admin', new DashboardType(context))
  app.$registry.register('admin', new UsersAdminType(context))
  app.$registry.register('admin', new GroupsAdminType(context))
  app.$registry.register('admin', new LicensesAdminType(context))
  app.$registry.register('exporter', new JSONTableExporter(context))
  app.$registry.register('exporter', new XMLTableExporter(context))

  registerRealtimeEvents(app.$realtime)

  // Overwrite the existing database application type with the one customized for
  // premium use.
  app.$registry.register(
    'application',
    new PremiumDatabaseApplicationType(context)
  )
}
