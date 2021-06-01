import { ApplicationType } from '@baserow/modules/core/applicationTypes'
import Sidebar from '@baserow/modules/database/components/sidebar/Sidebar'
import TemplateSidebar from '@baserow/modules/database/components/sidebar/TemplateSidebar'
import TableTemplate from '@baserow/modules/database/components/table/TableTemplate'
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

  getSidebarComponent() {
    return Sidebar
  }

  getTemplateSidebarComponent() {
    return TemplateSidebar
  }

  getTemplatesPageComponent() {
    return TableTemplate
  }

  getTemplatePage(application) {
    if (application.tables.length === 0) {
      return null
    }
    return {
      database: application,
      table: application.tables[0],
    }
  }

  getDependentsName() {
    return ['table', 'tables']
  }

  getDependents(database) {
    return database.tables.map((table) => {
      return {
        id: table.id,
        iconClass: 'table',
        name: table.name,
      }
    })
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
    const tables = application.tables
      .map((t) => t)
      .sort((a, b) => a.order - b.order)

    if (tables.length > 0) {
      $router.push({
        name: 'database-table',
        params: {
          databaseId: application.id,
          tableId: tables[0].id,
        },
      })
    } else {
      $store.dispatch('notification/error', {
        title: "Couldn't select the database.",
        message:
          "The database couldn't be selected because it doesn't have any tables. Use " +
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

  /**
   * It is not possible to update the tables by updating the application. In fact,
   * providing the tables as value could break the current table state. That is why
   * we remove it here.
   */
  prepareForStoreUpdate(application, data) {
    if (Object.prototype.hasOwnProperty.call(data, 'tables')) {
      delete data.tables
    }
    return data
  }
}
