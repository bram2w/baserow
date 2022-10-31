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

  getFeaturesDescription() {
    const { i18n } = this.app
    return i18n.t('enterprise.enterpriseFeatures')
  }

  getFeatures() {
    return [
      PremiumFeatures.PREMIUM,
      EnterpriseFeatures.RBAC,
      EnterpriseFeatures.SSO,
      EnterpriseFeatures.TEAMS,
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

  getSeatsManuallyAssigned() {
    return false
  }

  getLicenseDescription(license) {
    const { i18n } = this.app
    return i18n.t('enterprise.licenseDescription')
  }

  getLicenseSeatOverflowWarning(license) {
    const { i18n } = this.app
    return i18n.t('enterprise.overflowWarning')
  }
}
