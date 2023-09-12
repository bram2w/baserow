import { RowModalSidebarType } from '@baserow/modules/database/rowModalSidebarTypes'
import RowCommentsSidebar from '@baserow_premium/components/row_comments/RowCommentsSidebar'
import PremiumFeatures from '@baserow_premium/features'

export class CommentsRowModalSidebarType extends RowModalSidebarType {
  static getType() {
    return 'comments'
  }

  getName() {
    return this.app.i18n.t('rowCommentSidebar.name')
  }

  getComponent() {
    return RowCommentsSidebar
  }

  isDeactivated(database, table) {
    return !this.app.$hasPermission(
      'database.table.list_comments',
      table,
      database.workspace.id
    )
  }

  isSelectedByDefault(database) {
    return this.app.$hasFeature(PremiumFeatures.PREMIUM, database.workspace.id)
  }

  getOrder() {
    return 0
  }
}
