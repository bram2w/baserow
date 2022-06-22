import { BaserowPlugin } from '@baserow/modules/core/plugins'
import DatabaseDashboardSidebarLinks from '@baserow/modules/database/components/dashboard/DatabaseDashboardSidebarLinks'

export class DatabasePlugin extends BaserowPlugin {
  static getType() {
    return 'database'
  }

  getDashboardSidebarLinksComponent() {
    return DatabaseDashboardSidebarLinks
  }
}
