import WorkspaceService from '@baserow/modules/core/services/workspace'

/**
 * Mixin that fetches a workspace invitation based on the `workspaceInvitationToken` query
 * parameter. If the token is not found, null will be added as invitation data value.
 */
export default {
  async asyncData({ route, app }) {
    const token = route.query.workspaceInvitationToken

    if (token) {
      try {
        const { data: invitation } = await WorkspaceService(
          app.$client
        ).fetchInvitationByToken(token)
        return { invitation }
      } catch {}
    }

    return { invitation: null }
  },
}
