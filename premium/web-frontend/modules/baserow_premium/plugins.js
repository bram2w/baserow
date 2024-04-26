import { BaserowPlugin } from '@baserow/modules/core/plugins'
import PremiumTopSidebar from '@baserow_premium/components/sidebar/PremiumTopSidebar'
import BaserowLogoShareLinkOption from '@baserow_premium/components/views/BaserowLogoShareLinkOption'

export class PremiumPlugin extends BaserowPlugin {
  static getType() {
    return 'premium'
  }

  getSidebarTopComponent() {
    return PremiumTopSidebar
  }

  getAdditionalShareLinkOptions() {
    return [BaserowLogoShareLinkOption]
  }

  hasFeature(feature, forSpecificWorkspace) {
    return this.app.$licenseHandler.hasFeature(feature, forSpecificWorkspace)
  }

  /**
   * A hook to provide different action buttons to the premium features modal.
   */
  getPremiumModalButtonsComponent() {
    return null
  }
}
