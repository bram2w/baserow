import { Application } from '@/core/applications'
import Sidebar from '@/modules/database/components/Sidebar'

export class DatabaseApplication extends Application {
  getType() {
    return 'database'
  }

  getIconClass() {
    return 'database'
  }

  getName() {
    return 'Database'
  }

  getRouteName() {
    return 'application-database'
  }

  getSelectedSidebarComponent() {
    return Sidebar
  }
}
