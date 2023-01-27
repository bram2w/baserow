import { ViewOwnershipType } from '@baserow/modules/database/viewOwnershipTypes'
import PremiumFeatures from '@baserow_premium/features'

export class PersonalViewOwnershipType extends ViewOwnershipType {
  static getType() {
    return 'personal'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('viewOwnershipType.personal')
  }

  getIconClass() {
    return 'fas fa-lock'
  }

  isDeactivated(groupId) {
    return !this.app.$hasFeature(PremiumFeatures.PREMIUM, groupId)
  }

  getListViewTypeSort() {
    return 40
  }
}
