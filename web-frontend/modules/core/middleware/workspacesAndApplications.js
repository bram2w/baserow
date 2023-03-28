import { getWorkspaceCookie } from '@baserow/modules/core/utils/workspace'

/**
 * This middleware will make sure that all the workspaces and applications belonging to
 * the user are fetched and added to the store.
 */
export default async function WorkspacesAndApplications({ store, req, app }) {
  // If nuxt generate, pass this middleware
  if (process.server && !req) return

  // Get the selected workspace id
  let workspaceId = getWorkspaceCookie(app)

  // If the workspaces haven't already been selected we will
  if (store.getters['auth/isAuthenticated']) {
    // If the workspaces haven't been loaded we will load them all.
    if (!store.getters['workspace/isLoaded']) {
      await store.dispatch('workspace/fetchAll')

      // If the user only has one workspace we then that one must be selected.
      const workspaces = store.getters['workspace/getAll']
      if (store.getters['workspace/getAll'].length === 1) {
        workspaceId = workspaces[0].id
      }

      // If there is a workspaceId cookie we will select that workspace.
      if (workspaceId) {
        try {
          await store.dispatch('workspace/selectById', workspaceId)
        } catch {}
      }
    }
    // If the applications haven't been loaded we will also load them all.
    if (!store.getters['application/isLoaded']) {
      await store.dispatch('application/fetchAll')
    }
  }
}
