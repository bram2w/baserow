/***
 * Injects two functions for use globally:
 * - $hasFeature(FEATURE_STRING, OPTIONAL_GROUP_ID) -> bool
 *     Returns if the current user has access to the feature instance-wide if no group
 *     is supplied otherwise for the group if an id is provided.
 * - $highestLicenseType() -> LicenseType or null
 *     Returns the highest instance wide license the user has active or null if they
 *     do not have one.
 */
export default function ({ app }, inject) {
  const getters = app.store.getters
  const $registry = app.$registry

  /**
   * Returns a list of all active licenses the current user has instance wide.
   */
  function instanceWideLicenseTypes() {
    const instanceWideLicenses =
      getters['auth/getAdditionalUserData']?.active_licenses?.instance_wide ||
      {}
    return Object.entries(instanceWideLicenses)
      .filter(([key, enabled]) => enabled && $registry.exists('license', key))
      .map(([key, _]) => $registry.get('license', key))
  }

  /**
   * Returns the highest instance wide license type a user has or null if they have
   * none. The highest instance wide license is the one whose LicenseType.getOrder()
   * is the highest.
   */
  function highestInstanceWideLicenseType() {
    const orderedLicenses = instanceWideLicenseTypes().sort(
      (a, b) => b.getOrder() - a.getOrder()
    )
    if (orderedLicenses.length === 0) {
      return null
    } else {
      return orderedLicenses[0]
    }
  }

  /**
   * Returns any licenses the current user might have active for the specific group.
   */
  function getGroupLicenseTypes(groupId) {
    const perGroupLicenses =
      getters['auth/getAdditionalUserData']?.active_licenses?.per_group || {}
    return Object.entries(perGroupLicenses[groupId] || {})
      .filter(([key, enabled]) => enabled && $registry.exists('license', key))
      .map(([key, _]) => $registry.get('license', key))
  }

  function userHasFeatureEnabledInstanceWide(feature) {
    return instanceWideLicenseTypes().some((t) =>
      t.getFeatures().includes(feature)
    )
  }

  function userHasFeatureEnabledForGroupOnly(feature, groupId) {
    return getGroupLicenseTypes(groupId).some((t) =>
      t.getFeatures().includes(feature)
    )
  }

  function hasFeature(feature, forSpecificGroup = null) {
    return (
      userHasFeatureEnabledInstanceWide(feature) ||
      (forSpecificGroup
        ? userHasFeatureEnabledForGroupOnly(feature, forSpecificGroup)
        : false)
    )
  }
  inject('hasFeature', hasFeature)
  inject('highestLicenseType', highestInstanceWideLicenseType)
}
