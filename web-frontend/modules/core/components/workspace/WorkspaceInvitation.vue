<template>
  <Alert
    simple
    type="primary"
    icon="exclamation"
    :title="$t('workspaceInvitation.title')"
  >
    {{
      $t('workspaceInvitation.message', {
        by: invitation.invited_by,
        workspace: invitation.workspace,
      })
    }}
    <div v-if="invitation.message !== ''" class="quote">
      "{{ invitation.message }}"
    </div>
    <br />
    <a
      class="button button--error dashboard__alert-button"
      :class="{ 'button--loading': rejectLoading }"
      :disabled="rejectLoading || acceptLoading"
      @click="!rejectLoading && !acceptLoading && reject(invitation)"
      >{{ $t('workspaceInvitation.reject') }}</a
    >
    <a
      class="button button--success dashboard__alert-button"
      :class="{ 'button--loading': acceptLoading }"
      :disabled="rejectLoading || acceptLoading"
      @click="!rejectLoading && !acceptLoading && accept(invitation)"
      >{{ $t('workspaceInvitation.accept') }}</a
    >
  </Alert>
</template>

<script>
import WorkspaceService from '@baserow/modules/core/services/workspace'
import ApplicationService from '@baserow/modules/core/services/application'
import { notifyIf } from '@baserow/modules/core/utils/error'

export default {
  name: 'WorkspaceInvitation',
  props: {
    invitation: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      rejectLoading: false,
      acceptLoading: false,
    }
  },
  methods: {
    async reject(invitation) {
      this.rejectLoading = true

      try {
        await WorkspaceService(this.$client).rejectInvitation(invitation.id)
        this.$emit('remove', invitation)
      } catch (error) {
        this.rejectLoading = false
        notifyIf(error, 'workspace')
      }
    },
    /**
     * Accepts the invitation to join the workspace and populates the stores with the new
     * workspace and applications.
     */
    async accept(invitation) {
      this.acceptLoading = true

      try {
        const { data: workspace } = await WorkspaceService(
          this.$client
        ).acceptInvitation(invitation.id)

        // The accept endpoint returns a workspace user object that we can add to the
        // store. Also the applications that we just fetched can be added to the
        // store.
        await this.$store.dispatch('workspace/forceCreate', workspace)
        await this.$store.dispatch('workspace/fetchPermissions', workspace)
        await this.$store.dispatch('workspace/fetchRoles', workspace)

        if (
          this.$hasPermission(
            'workspace.list_applications',
            workspace,
            workspace.id
          )
        ) {
          // After the invitation is accepted and workspace is received we can immediately
          // fetch the applications that belong to the workspace.
          const { data: applications } = await ApplicationService(
            this.$client
          ).fetchAll(workspace.id)

          applications.forEach((application) => {
            this.$store.dispatch('application/forceCreate', application)
          })
        }
        this.$emit('remove', invitation)
      } catch (error) {
        this.acceptLoading = false
        notifyIf(error, 'workspace')
      }
    },
  },
}
</script>
