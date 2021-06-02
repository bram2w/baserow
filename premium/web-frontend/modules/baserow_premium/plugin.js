import { PremiumPlugin } from '@baserow_premium/plugins'
import {
  JSONTableExporter,
  XMLTableExporter,
} from '@baserow_premium/tableExporterTypes'
import {
  DashboardType,
  UsersAdminType,
  GroupsAdminType,
} from '@baserow_premium/adminTypes'

export default ({ app }) => {
  app.$registry.register('plugin', new PremiumPlugin())
  app.$registry.register('admin', new DashboardType())
  app.$registry.register('admin', new UsersAdminType())
  app.$registry.register('admin', new GroupsAdminType())
  app.$registry.register('exporter', new JSONTableExporter())
  app.$registry.register('exporter', new XMLTableExporter())
}
