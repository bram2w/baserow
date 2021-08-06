import RowCommentsSidebar from '@baserow_premium/components/row_comments/RowCommentsSidebar'
import { DatabaseApplicationType } from '@baserow/modules/database/applicationTypes'
import GridViewRowExpandButtonWithCommentCount from '@baserow_premium/components/row_comments/GridViewRowExpandButtonWithCommentCount'

export class PremiumDatabaseApplicationType extends DatabaseApplicationType {
  getRowEditModalRightSidebarComponent() {
    return RowCommentsSidebar
  }

  getRowExpandButtonComponent() {
    return GridViewRowExpandButtonWithCommentCount
  }
}
