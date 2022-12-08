export class LicenseHandler {
  constructor(app) {
    this.getters = app.store.getters
    this.dispatch = app.store.dispatch
    this.$registry = app.$registry
    this.app = app
  }

  listenToBusEvents() {
    return this.app.$bus.$on(
      'user-data-updated',
      this.afterUserDataUpdate.bind(this)
    )
  }

  /**
   * Triggers updates to any frontend stores that might need updating if a license
   * has changed.
   */
  async afterUserDataUpdate(updatedUserData) {
    if (updatedUserData?.active_licenses?.instance_wide) {
      // There has been some update to an instance wide license, force all groups
      // to refresh their roles
      for (const group of this.getters['group/getAll']) {
        await this.dispatch('group/forceRefreshRoles', group)
      }
    } else {
      // Otherwise only update the groups for whom their active licenses have changed.
      for (const groupId of Object.keys(
        updatedUserData?.active_licenses?.per_group || {}
      )) {
        const group = this.getters['group/get'](parseInt(groupId))
        if (group) {
          await this.dispatch('group/forceRefreshRoles', group)
        }
      }
    }
  }

  /**
   * Returns a list of all active licenses the current user has instance wide.
   */
  instanceWideLicenseTypes() {
    const userData = this.getters['auth/getAdditionalUserData']
    const instanceWideLicenses = userData?.active_licenses?.instance_wide || {}
    return Object.entries(instanceWideLicenses)
      .filter(
        ([key, enabled]) => enabled && this.$registry.exists('license', key)
      )
      .map(([key, _]) => this.$registry.get('license', key))
  }

  /**
   * Returns the highest instance wide license type a user has or null if they have
   * none. The highest instance wide license is the one whose LicenseType.getOrder()
   * is the highest.
   */
  highestInstanceWideLicenseType() {
    const orderedLicenses = this.instanceWideLicenseTypes().sort(
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
  getGroupLicenseTypes(groupId) {
    const perGroupLicenses =
      this.getters['auth/getAdditionalUserData']?.active_licenses?.per_group ||
      {}
    return Object.entries(perGroupLicenses[groupId] || {})
      .filter(
        ([key, enabled]) => enabled && this.$registry.exists('license', key)
      )
      .map(([key, _]) => this.$registry.get('license', key))
  }

  userHasFeatureEnabledInstanceWide(feature) {
    return this.instanceWideLicenseTypes().some((t) =>
      t.getFeatures().includes(feature)
    )
  }

  userHasFeatureEnabledForGroupOnly(feature, groupId) {
    return this.getGroupLicenseTypes(groupId).some((t) =>
      t.getFeatures().includes(feature)
    )
  }

  hasFeature(feature, forSpecificGroup = null) {
    return (
      this.userHasFeatureEnabledInstanceWide(feature) ||
      (forSpecificGroup
        ? this.userHasFeatureEnabledForGroupOnly(feature, forSpecificGroup)
        : false)
    )
  }
}
