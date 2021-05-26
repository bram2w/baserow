import { PremPlugin } from '@baserow_premium/plugins'
import { DashboardType, UsersAdminType } from '@baserow_premium/adminTypes'

export default ({ app }) => {
  app.$registry.register('plugin', new PremPlugin())
  app.$registry.register('admin', new DashboardType())
  app.$registry.register('admin', new UsersAdminType())
}
