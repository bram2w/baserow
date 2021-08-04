import { PremiumPlugin } from '@baserow_premium/plugins'
import {
  JSONTableExporter,
  XMLTableExporter,
} from '@baserow_premium/tableExporterTypes'
import {
  DashboardType,
  GroupsAdminType,
  UsersAdminType,
} from '@baserow_premium/adminTypes'
import rowCommentsStore from '@baserow_premium/store/row_comments'
import { PremiumDatabaseApplicationType } from '@baserow_premium/applicationTypes'

export default ({ store, app }) => {
  store.registerModule('row_comments', rowCommentsStore)

  app.$registry.register('plugin', new PremiumPlugin())
  app.$registry.register('admin', new DashboardType())
  app.$registry.register('admin', new UsersAdminType())
  app.$registry.register('admin', new GroupsAdminType())
  app.$registry.register('exporter', new JSONTableExporter())
  app.$registry.register('exporter', new XMLTableExporter())

  // Overwrite the existing database application type with the one customized for
  // premium use.
  app.$registry.register('application', new PremiumDatabaseApplicationType())
}
