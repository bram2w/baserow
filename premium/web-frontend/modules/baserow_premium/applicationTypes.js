import { DatabaseApplicationType } from '@baserow/modules/database/applicationTypes'
import GridViewRowExpandButtonWithCommentCount from '@baserow_premium/components/row_comments/GridViewRowExpandButtonWithCommentCount'

export class PremiumDatabaseApplicationType extends DatabaseApplicationType {
  getRowExpandButtonComponent() {
    return GridViewRowExpandButtonWithCommentCount
  }
}
