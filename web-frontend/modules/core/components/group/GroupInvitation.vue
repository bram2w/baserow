<template>
  <Alert
    simple
    type="primary"
    icon="exclamation"
    :title="$t('groupInvitation.title')"
  >
    {{
      $t('groupInvitation.message', {
        by: invitation.invited_by,
        group: invitation.group,
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
      >{{ $t('groupInvitation.reject') }}</a
    >
    <a
      class="button button--success dashboard__alert-button"
      :class="{ 'button--loading': acceptLoading }"
      :disabled="rejectLoading || acceptLoading"
      @click="!rejectLoading && !acceptLoading && accept(invitation)"
      >{{ $t('groupInvitation.accept') }}</a
    >
  </Alert>
</template>

<script>
import GroupService from '@baserow/modules/core/services/group'
import ApplicationService from '@baserow/modules/core/services/application'
import { notifyIf } from '@baserow/modules/core/utils/error'

export default {
  name: 'GroupInvitation',
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
        await GroupService(this.$client).rejectInvitation(invitation.id)
        this.$emit('remove', invitation)
      } catch (error) {
        this.rejectLoading = false
        notifyIf(error, 'group')
      }
    },
    /**
     * Accepts the invitation to join the group and populates the stores with the new
     * group and applications.
     */
    async accept(invitation) {
      this.acceptLoading = true

      try {
        const { data: group } = await GroupService(
          this.$client
        ).acceptInvitation(invitation.id)

        // The accept endpoint returns a group user object that we can add to the
        // store. Also the applications that we just fetched can be added to the
        // store.
        await this.$store.dispatch('group/forceCreate', group)
        await this.$store.dispatch('group/fetchPermissions', group)
        await this.$store.dispatch('group/fetchRoles', group)

        if (this.$hasPermission('group.list_applications', group, group.id)) {
          // After the invitation is accepted and group is received we can immediately
          // fetch the applications that belong to the group.
          const { data: applications } = await ApplicationService(
            this.$client
          ).fetchAll(group.id)

          applications.forEach((application) => {
            this.$store.dispatch('application/forceCreate', application)
          })
        }
        this.$emit('remove', invitation)
      } catch (error) {
        this.acceptLoading = false
        notifyIf(error, 'group')
      }
    },
  },
}
</script>
