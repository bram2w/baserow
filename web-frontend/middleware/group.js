import { getGroupCookie, unsetGroupCookie } from '@/utils/group'

/**
 * This middleware checks if there is a saved group id in the cookies. If set
 * it will fetch the groups, and related application of that group.
 */
export default function({ store, req, app }) {
  // If nuxt generate, pass this middleware
  if (process.server && !req) return

  // Get the selected group id
  const groupId = getGroupCookie(app.$cookies)

  // If a group id cookie is set, the user is authenticated and a selected group
  // is not already set then we will fetch the groups and select that group.
  if (
    groupId &&
    store.getters['auth/isAuthenticated'] &&
    !store.getters['group/hasSelected']
  ) {
    return store
      .dispatch('group/fetchAll')
      .catch(() => {
        unsetGroupCookie(app.$cookies)
      })
      .then(() => {
        const group = store.getters['group/get'](groupId)
        if (group) {
          return store.dispatch('group/select', group)
        }
      })
  }
}
