import { lazyComponent } from '@baserow/modules/core/utils/lazyComponent'
import { BaserowPlugin } from '@baserow/modules/core/plugins'

const DatabaseDashboardResourceLinks = lazyComponent(
  () =>
    import('@baserow/modules/database/components/dashboard/DatabaseDashboardResourceLinks')
)

export class DatabasePlugin extends BaserowPlugin {
  static getType() {
    return 'database'
  }

  getDashboardResourceLinksComponent() {
    return DatabaseDashboardResourceLinks
  }
}
