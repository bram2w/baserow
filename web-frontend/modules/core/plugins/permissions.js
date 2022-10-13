export default function ({ app }, inject) {
  /**
   * Check the permission for the given operation with the given context.
   *
   * This function uses all the registered permissions to check the permission.
   * @param {string} operation
   * @param {object} context
   * @returns True ift he operation is permitted, false otherwise.
   */
  const hasPermission = (operation, context) => {
    const { store, $registry } = app

    const loaded = store.getters['permissions/isLoaded']
    if (!loaded) {
      return false
    }

    const perms = store.getters['permissions/get']

    // Check all permission managers whether one accepts or refuses the operation
    for (const perm of perms) {
      const { name, permissions } = perm
      const manager = $registry.get('permissionManager', name)
      const result = manager.hasPermission(permissions, operation, context)

      if ([true, false].includes(result)) {
        return result
      }
    }
    return false
  }
  inject('hasPermission', hasPermission)
}
