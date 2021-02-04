import GroupService from '@baserow/modules/core/services/group'

/**
 * Mixin that fetches a group invitation based on the `groupInvitationToken` query
 * parameter. If the token is not found, null will be added as invitation data value.
 */
export default {
  async asyncData({ route, app }) {
    const token = route.query.groupInvitationToken

    if (token) {
      try {
        const { data: invitation } = await GroupService(
          app.$client
        ).fetchInvitationByToken(token)
        return { invitation }
      } catch {}
    }

    return { invitation: null }
  },
}
