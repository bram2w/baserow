import { Registerable } from '@baserow/modules/core/registry'

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
   * When a license of this type is active if the user should have access to
   * premium features.
   */
  hasPremiumFeatures() {
    throw new Error('Must be set by the implementing sub class.')
  }

  /**
   * Returns if this license type is currently active and valid globally if no
   * group is provided, or active specifically for the provided group.
   * Otherwise returns null if no license is active.
   *
   * @param forGroupId An optional group id to check more specifically if licenses can
   *  be activated per group.
   */
  hasValidActiveLicense(forGroupId = undefined) {
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

  hasPremiumFeatures() {
    return true
  }

  hasValidActiveLicense(forGroupId = undefined) {
    const additionalUserData =
      this.app.store.getters['auth/getAdditionalUserData']
    const validLicense = additionalUserData?.premium?.valid_license
    const groups = Array.isArray(validLicense)
      ? validLicense.filter((o) => o.type === 'group').map((o) => o.id)
      : []
    return (
      validLicense === true ||
      (Array.isArray(validLicense) && groups.includes(forGroupId))
    )
  }
}
