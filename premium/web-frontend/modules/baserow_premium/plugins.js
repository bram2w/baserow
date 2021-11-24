import { BaserowPlugin } from '@baserow/modules/core/plugins'

export class PremiumPlugin extends BaserowPlugin {
  static getType() {
    return 'premium'
  }

  static hasValidPremiumLicense(additionalUserData) {
    return additionalUserData.premium.valid_license
  }
}
