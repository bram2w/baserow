import { BaserowPlugin } from '@baserow/modules/core/plugins'
import PremiumTopSidebar from '@baserow_premium/components/sidebar/PremiumTopSidebar'

export class PremiumPlugin extends BaserowPlugin {
  static getType() {
    return 'premium'
  }

  /**
   * @param additionalUserData The additional user data that contains to which group
   * the user has a premium license for.
   * @param forGroup If provided, the user must explicitly have an active license
   * for that group or for all groups.
   * @return boolean
   */
  static hasValidPremiumLicense(additionalUserData, forGroupId = undefined) {
    const validLicense = additionalUserData?.premium?.valid_license
    const groups = Array.isArray(validLicense)
      ? validLicense.filter((o) => o.type === 'group').map((o) => o.id)
      : []
    return (
      validLicense === true ||
      (Array.isArray(validLicense) && groups.includes(forGroupId))
    )
  }

  getSidebarTopComponent() {
    return PremiumTopSidebar
  }
}
