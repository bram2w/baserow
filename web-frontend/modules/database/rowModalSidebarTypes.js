import { Registerable } from '@baserow/modules/core/registry'
import RowHistorySidebar from '@baserow/modules/database/components/row/RowHistorySidebar.vue'

export class RowModalSidebarType extends Registerable {
  /**
   * A human readable name
   */
  getName() {
    return null
  }

  /**
   * The component to render in the sidebar
   */
  getComponent() {
    return null
  }

  /**
   * Whether the sidebar component should be shown
   */
  isDeactivated(database, table) {
    return false
  }

  /**
   * When true, the sidebar type indicates
   * that it should be focused first.
   */
  isSelectedByDefault(database) {
    return false
  }

  getOrder() {
    return 50
  }
}

export class HistoryRowModalSidebarType extends RowModalSidebarType {
  static getType() {
    return 'history'
  }

  getName() {
    return this.app.i18n.t('rowHistorySidebar.name')
  }

  getComponent() {
    return RowHistorySidebar
  }

  isDeactivated(database, table) {
    const hasPermissions = this.app.$hasPermission(
      'database.table.read_row_history',
      table,
      database.workspace.id
    )
    return !hasPermissions
  }

  isSelectedByDefault(database) {
    return true
  }

  getOrder() {
    return 10
  }
}
