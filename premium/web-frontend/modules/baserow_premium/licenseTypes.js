import { Registerable } from '@baserow/modules/core/registry'
import PremiumFeatures from '@baserow_premium/features'

/**
 *
 */
export class LicenseType extends Registerable {
  /**
   * A human readable name of the license type.
   */
  getName() {
    return null
  }

  /**
   * The css class that should be applied when rendering the badge of a license of
   * this type.
   */
  getLicenseBadgeClass() {
    throw new Error('Must be set by the implementing sub class.')
  }

  /**
   * The a list of features that this license provides.
   */
  getFeatures() {
    throw new Error('Must be set by the implementing sub class.')
  }

  getFeaturesDescription() {
    return this.getName() + ' Features'
  }

  showInTopSidebarWhenActive() {
    throw new Error('Must be set by the implementing sub class.')
  }

  getTopSidebarTooltip() {
    throw new Error('Must be set by the implementing sub class.')
  }

  getOrder() {
    throw new Error('Must be set by the implementing sub class.')
  }

  getSeatsManuallyAssigned() {
    throw new Error('Must be set by the implementing sub class.')
  }

  getLicenseDescription(license) {
    throw new Error('Must be set by the implementing sub class.')
  }

  getLicenseSeatOverflowWarning(license) {
    throw new Error('Must be set by the implementing sub class.')
  }
}

export class PremiumLicenseType extends LicenseType {
  static getType() {
    return 'premium'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('licenses.premium')
  }

  getLicenseBadgeClass() {
    return 'license-plan--premium'
  }

  getFeatures() {
    return [PremiumFeatures.PREMIUM]
  }

  getFeaturesDescription() {
    const { i18n } = this.app
    return i18n.t('licenses.premiumFeatures')
  }

  getTopSidebarTooltip() {
    const { i18n } = this.app
    return i18n.t('premiumTopSidebar.premium')
  }

  showInTopSidebarWhenActive() {
    return true
  }

  getOrder() {
    return 10
  }

  getSeatsManuallyAssigned() {
    return true
  }

  getLicenseDescription(license) {
    const { i18n } = this.app
    return i18n.t('license.description', license)
  }

  getLicenseSeatOverflowWarning(license) {
    return ''
  }
}
