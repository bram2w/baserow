import { BaserowPlugin } from '@baserow/modules/core/plugins'
import PremiumTopSidebar from '@baserow_premium/components/sidebar/PremiumTopSidebar'
import BaserowLogoShareLinkOption from '@baserow_premium/components/views/BaserowLogoShareLinkOption'

export class PremiumPlugin extends BaserowPlugin {
  static getType() {
    return 'premium'
  }

  getValidActiveLicense(forGroupId = undefined) {
    for (const licenseType of Object.values(
      this.app.$registry.getAll('license')
    )) {
      if (licenseType.hasValidActiveLicense(forGroupId)) {
        return licenseType
      }
    }
    return null
  }

  activeLicenseHasPremiumFeatures(forGroupId = undefined) {
    const optionalActiveLicenseType = this.getValidActiveLicense(forGroupId)
    if (optionalActiveLicenseType) {
      return optionalActiveLicenseType.hasPremiumFeatures()
    } else {
      return false
    }
  }

  getSidebarTopComponent() {
    return PremiumTopSidebar
  }

  getAdditionalShareLinkOptions() {
    return [BaserowLogoShareLinkOption]
  }
}
