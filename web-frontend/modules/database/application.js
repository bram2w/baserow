import { Application } from '@/core/applications'
import Sidebar from '@/modules/database/components/Sidebar'
import { populateTable } from '@/modules/database/store/table'

export class DatabaseApplication extends Application {
  static getType() {
    return 'database'
  }

  getType() {
    return DatabaseApplication.getType()
  }

  getIconClass() {
    return 'database'
  }

  getName() {
    return 'Database'
  }

  getSelectedSidebarComponent() {
    return Sidebar
  }

  populate(application) {
    const values = super.populate(application)
    values.tables.forEach((object, index, tables) => populateTable(object))
    return values
  }
}
