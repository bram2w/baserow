<template>
  <Modal>
    <h2 class="box__title">
      {{ $t('membersSettings.membersInviteModal.title') }}
    </h2>
    <Error :error="error"></Error>
    <GroupInviteForm
      ref="inviteForm"
      :group="group"
      @submitted="inviteSubmitted"
    >
      <div class="col col-12 align-right">
        <button
          :class="{ 'button--loading': inviteLoading }"
          class="button"
          :disabled="inviteLoading"
        >
          {{ $t('membersSettings.membersInviteModal.submit') }}
        </button>
      </div>
    </GroupInviteForm>
  </Modal>
</template>

<script>
import modal from '@baserow/modules/core/mixins/modal'
import error from '@baserow/modules/core/mixins/error'
import GroupInviteForm from '@baserow/modules/core/components/group/GroupInviteForm'
import GroupService from '@baserow/modules/core/services/group'
import { ResponseErrorMessage } from '@baserow/modules/core/plugins/clientHandler'

export default {
  name: 'MembersInviteModal',
  components: { GroupInviteForm },
  mixins: [modal, error],
  props: {
    group: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      inviteLoading: false,
    }
  },
  methods: {
    async inviteSubmitted(values) {
      this.inviteLoading = true

      try {
        // The public accept url is the page where the user can publicly navigate too,
        // to accept the group invitation.
        const acceptUrl = `${this.$env.PUBLIC_WEB_FRONTEND_URL}/group-invitation`
        await GroupService(this.$client).sendInvitation(
          this.group.id,
          acceptUrl,
          values
        )
        this.$refs.inviteForm.reset()
        this.$emit('invite-submitted')
        this.hide()
      } catch (error) {
        this.handleError(error, 'group', {
          ERROR_GROUP_USER_ALREADY_EXISTS: new ResponseErrorMessage(
            this.$t(
              'membersSettings.membersInviteModal.errors.userAlreadyInGroup.title'
            ),
            this.$t(
              'membersSettings.membersInviteModal.errors.userAlreadyInGroup.text'
            )
          ),
        })
      }

      this.inviteLoading = false
    },
  },
}
</script>
