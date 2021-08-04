import RowCommentsSidebar from '@baserow_premium/components/row_comments/RowCommentsSidebar'
import { DatabaseApplicationType } from '@baserow/modules/database/applicationTypes'

export class PremiumDatabaseApplicationType extends DatabaseApplicationType {
  getRowEditModalRightSidebarComponent() {
    return RowCommentsSidebar
  }
}
