import { ViewOwnershipType } from '@baserow/modules/database/viewOwnershipTypes'
import PremiumFeatures from '@baserow_premium/features'
import PremiumModal from '@baserow_premium/components/PremiumModal'

export class PersonalViewOwnershipType extends ViewOwnershipType {
  static getType() {
    return 'personal'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('viewOwnershipType.personal')
  }

  getFeatureName() {
    const { i18n } = this.app
    return i18n.t('premiumFeatures.personalViews')
  }

  getIconClass() {
    return 'fas fa-lock'
  }

  isDeactivated(workspaceId) {
    return !this.app.$hasFeature(PremiumFeatures.PREMIUM, workspaceId)
  }

  getDeactivatedText() {
    return this.app.i18n.t('premium.deactivated')
  }

  getDeactivatedModal() {
    return PremiumModal
  }

  getListViewTypeSort() {
    return 40
  }
}
