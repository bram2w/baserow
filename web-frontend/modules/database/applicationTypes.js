import { ApplicationType } from '@baserow/modules/core/applicationTypes'
import Sidebar from '@baserow/modules/database/components/Sidebar'
import { populateTable } from '@baserow/modules/database/store/table'

export class DatabaseApplicationType extends ApplicationType {
  static getType() {
    return 'database'
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

  /**
   * When a table of the deleted database is selected we must redirect back to
   * the dashboard because that page doesn't exist anymore.
   */
  delete(application, { $router }) {
    const tableSelected = application.tables.some((table) => table._.selected)
    if (tableSelected) {
      $router.push({ name: 'dashboard' })
    }
  }

  select(application, { $router, $store }) {
    if (application.tables.length > 0) {
      $router.push({
        name: 'database-table',
        params: {
          databaseId: application.id,
          tableId: application.tables[0].id,
        },
      })
    } else {
      $store.dispatch('notification/error', {
        title: 'Could select the database.',
        message:
          "The database could be selected because it doesn't have any tables. Use " +
          'the sidebar to create one.',
      })
    }
  }

  /**
   * When another database is selected in the sidebar we have the change the
   * selected state of all the table children.
   */
  clearChildrenSelected(application) {
    Object.values(application.tables).forEach((table) => {
      if (table._.selected) {
        table._.selected = false
      }
    })
  }
}
