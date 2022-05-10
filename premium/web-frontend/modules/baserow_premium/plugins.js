import { BaserowPlugin } from '@baserow/modules/core/plugins'
import IsImpersonating from '@baserow_premium/components/sidebar/IsImpersonating'

export class PremiumPlugin extends BaserowPlugin {
  static getType() {
    return 'premium'
  }

  static hasValidPremiumLicense(additionalUserData) {
    return additionalUserData?.premium?.valid_license
  }

  getSidebarTopComponent() {
    return IsImpersonating
  }
}
