import { PremiumPlugin } from '@baserow_premium/plugins'
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
}
