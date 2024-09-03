import { BaserowPlugin } from '@baserow/modules/core/plugins'
import DatabaseDashboardResourceLinks from '@baserow/modules/database/components/dashboard/DatabaseDashboardResourceLinks'

export class DatabasePlugin extends BaserowPlugin {
  static getType() {
    return 'database'
  }

  getDashboardResourceLinksComponent() {
    return DatabaseDashboardResourceLinks
  }
}
