import EnterpriseFeatures from '@baserow_enterprise/features'
import PremiumFeatures from '@baserow_premium/features'
import { LicenseType } from '@baserow_premium/licenseTypes'
export class EnterpriseLicenseType extends LicenseType {
  static getType() {
    return 'enterprise'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('enterprise.license')
  }

  getLicenseBadgeClass() {
    return 'license-plan--enterprise'
  }

  getFeatures() {
    return [
      PremiumFeatures.PREMIUM,
      EnterpriseFeatures.RBAC,
      EnterpriseFeatures.SSO,
    ]
  }

  getTopSidebarTooltip() {
    const { i18n } = this.app
    return i18n.t('enterprise.sidebarTooltip')
  }

  showInTopSidebarWhenActive() {
    return true
  }

  getOrder() {
    return 100
  }
}
