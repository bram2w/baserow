<script>
import WorkspaceService from '@baserow/modules/core/services/workspace'

export default {
  middleware: ['authentication'],
  async asyncData({ store, params, error, app, redirect }) {
    const { token } = params
    let invitation

    try {
      const { data } = await WorkspaceService(
        app.$client
      ).fetchInvitationByToken(token)
      invitation = data
    } catch {
      return error({ statusCode: 404, message: 'Invitation not found.' })
    }

    // If the authenticated user has the same email access we can accept the invitation
    // right away and redirect to the dashboard.
    if (
      store.getters['auth/isAuthenticated'] &&
      store.getters['auth/getUsername'] === invitation.email
    ) {
      await WorkspaceService(app.$client).acceptInvitation(invitation.id)
      return redirect({ name: 'dashboard' })
    }

    // Depending on if the email address already exist we redirect the user to either
    // the login or redirect page.
    const name = invitation.email_exists ? 'login' : 'signup'
    return redirect({ name, query: { workspaceInvitationToken: token } })
  },
}
</script>
