import { getGroupCookie } from '@baserow/modules/core/utils/group'

/**
 * This middleware will make sure that all the groups and applications belonging to
 * the user are fetched and added to the store.
 */
export default async function({ store, req, app }) {
  // If nuxt generate, pass this middleware
  if (process.server && !req) return

  // Get the selected group id
  const groupId = getGroupCookie(app.$cookies)

  // If the groups haven't already been selected we will
  if (store.getters['auth/isAuthenticated']) {
    // If the groups haven't been loaded we will load them all.
    if (!store.getters['group/isLoaded']) {
      await store.dispatch('group/fetchAll')

      // If there is a groupId cookie we will select that group.
      if (groupId) {
        await store.dispatch('group/selectById', groupId)
      }
    }
    // If the applications haven't been loaded we will also load them all.
    if (!store.getters['application/isLoaded']) {
      await store.dispatch('application/fetchAll')
    }
  }
}
