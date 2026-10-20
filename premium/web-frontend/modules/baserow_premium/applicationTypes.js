import { lazyComponent } from '@baserow/modules/core/utils/lazyComponent'
import { DatabaseApplicationType } from '@baserow/modules/database/applicationTypes'

const GridViewRowExpandButtonWithCommentCount = lazyComponent(
  () =>
    import('@baserow_premium/components/row_comments/GridViewRowExpandButtonWithCommentCount')
)

export class PremiumDatabaseApplicationType extends DatabaseApplicationType {
  getRowExpandButtonComponent() {
    return GridViewRowExpandButtonWithCommentCount
  }
}
