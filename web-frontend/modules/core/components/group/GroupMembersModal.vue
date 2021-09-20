<template>
  <Modal @show="initialize">
    <h2 class="box__title">
      {{ $t('groupMemberModal.membersModalTitle', { group: group.name }) }}
    </h2>
    <Error :error="error"></Error>
    <GroupInviteForm ref="inviteForm" @submitted="inviteSubmitted">
      <div class="col col-12 align-right">
        <button
          :class="{ 'button--loading': inviteLoading }"
          class="button"
          :disabled="inviteLoading"
        >
          {{ $t('groupMemberModal.sendInvite') }}
        </button>
      </div>
    </GroupInviteForm>
    <div v-if="loading" class="loading"></div>
    <div v-else-if="!loading">
      <div
        v-if="users.length > 0 || invitations.length > 0"
        class="separator"
      ></div>
      <GroupMember
        v-for="user in users"
        :id="user.id"
        :key="'user-' + user.id"
        :name="user.name"
        :description="getUserDescription(user)"
        :permissions="user.permissions"
        :loading="user._.loading"
        :disabled="user.email === username"
        @updated="updateUser(user, $event)"
        @removed="removeUser(user)"
      ></GroupMember>
      <GroupMember
        v-for="invitation in invitations"
        :id="invitation.id"
        :ref="'invitation-' + invitation.id"
        :key="'invitation-' + invitation.id"
        :name="invitation.email"
        :description="getInvitationDescription(invitation)"
        :permissions="invitation.permissions"
        :loading="invitation._.loading"
        @updated="updateInvitation(invitation, $event)"
        @removed="removeInvitation(invitation)"
      ></GroupMember>
    </div>
  </Modal>
</template>

<script>
import { mapGetters } from 'vuex'

import moment from '@baserow/modules/core/moment'
import modal from '@baserow/modules/core/mixins/modal'
import error from '@baserow/modules/core/mixins/error'
import { notifyIf } from '@baserow/modules/core/utils/error'
import { ResponseErrorMessage } from '@baserow/modules/core/plugins/clientHandler'
import GroupService from '@baserow/modules/core/services/group'
import GroupInviteForm from '@baserow/modules/core/components/group/GroupInviteForm'
import GroupMember from '@baserow/modules/core/components/group/GroupMember'

function populateUser(user) {
  user._ = { loading: false }
  return user
}

function populateInvitation(invitation) {
  invitation._ = { loading: false }
  return invitation
}

export default {
  name: 'CreateGroupModal',
  components: { GroupMember, GroupInviteForm },
  mixins: [modal, error],
  props: {
    group: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      users: [],
      invitations: [],
      loading: false,
      inviteLoading: false,
    }
  },
  computed: {
    ...mapGetters({
      username: 'auth/getUsername',
    }),
  },
  methods: {
    /**
     * The initialize method is called when the modal opens. It will fetch all the
     * users and invitations of the group.
     */
    async initialize() {
      this.hideError()
      this.loading = true
      this.users = []
      this.invitations = []

      try {
        const users = await GroupService(this.$client).fetchAllUsers(
          this.group.id
        )
        const invitations = await GroupService(
          this.$client
        ).fetchAllInvitations(this.group.id)

        this.users = users.data.map(populateUser)
        this.invitations = invitations.data.map(populateInvitation)
      } catch (error) {
        this.handleError(error, 'group')
      }

      this.loading = false
    },
    /**
     * Called when the group invitation form is submitted. It will send a request to
     * the backend which will create a new group invitations.
     */
    async inviteSubmitted(values) {
      this.inviteLoading = true

      try {
        // The public accept url is the page where the user can publicly navigate too,
        // to accept the group invitation.
        const acceptUrl = `${this.$env.PUBLIC_WEB_FRONTEND_URL}/group-invitation`
        const { data } = await GroupService(this.$client).sendInvitation(
          this.group.id,
          acceptUrl,
          values
        )
        this.$refs.inviteForm.reset()

        const invitation = populateInvitation(data)

        // It could be that the an invitation for the email address already exists, in
        // that case we want to update the invitation instead of adding it to the list.
        const index = this.invitations.findIndex((i) => i.id === data.id)
        if (index !== -1) {
          this.invitations[index] = invitation
        } else {
          this.invitations.push(invitation)
        }

        this.$nextTick(() => {
          this.highlightInvitation(invitation)
        })
      } catch (error) {
        this.handleError(error, 'group', {
          ERROR_GROUP_USER_ALREADY_EXISTS: new ResponseErrorMessage(
            this.$t('groupMemberModal.userAlreadyInGroupTitle'),
            this.$t('groupMemberModal.userAlreadyInGroupText')
          ),
        })
      }

      this.inviteLoading = false
    },
    highlightInvitation(invitation) {
      const name = 'invitation-' + invitation.id

      if (!Object.prototype.hasOwnProperty.call(this.$refs, name)) {
        return
      }

      this.$refs[name][0].highlight()
    },
    getUserDescription(user) {
      return this.$t('groupMemberModal.userDescription', {
        user: user.email,
        since: moment(user.created_on).fromNow(true),
      })
    },
    async updateUser(user, { permissions }) {
      if (user.permissions === permissions) {
        return
      }

      this.hideError()
      const oldPermissions = user.permissions
      user.permissions = permissions

      try {
        await GroupService(this.$client).updateUser(user.id, { permissions })
      } catch (error) {
        user.permissions = oldPermissions
        notifyIf(error, 'group')
      }
    },
    async removeUser(user) {
      this.hideError()
      user._.loading = true

      try {
        await GroupService(this.$client).deleteUser(user.id)
        const index = this.users.findIndex((u) => u.id === user.id)
        this.users.splice(index, 1)
      } catch (error) {
        user._.loading = false
        notifyIf(error, 'group')
      }
    },
    getInvitationDescription(invitation) {
      return this.$t('groupMemberModal.invitationDescription', {
        since: moment(invitation.created_on).fromNow(true),
      })
    },
    async updateInvitation(invitation, { permissions }) {
      if (invitation.invitation === permissions) {
        return
      }

      this.hideError()
      const oldPermissions = invitation.permissions
      invitation.permissions = permissions

      try {
        await GroupService(this.$client).updateInvitation(invitation.id, {
          permissions,
        })
      } catch (error) {
        invitation.permissions = oldPermissions
        notifyIf(error, 'group')
      }
    },
    async removeInvitation(invitation) {
      this.hideError()
      invitation._.loading = true

      try {
        await GroupService(this.$client).deleteInvitation(invitation.id)
        const index = this.invitations.findIndex((i) => i.id === invitation.id)
        this.invitations.splice(index, 1)
      } catch (error) {
        invitation._.loading = false
        notifyIf(error, 'group')
      }
    },
  },
}
</script>

<i18n>
{
  "en": {
    "groupMemberModal": {
      "membersModalTitle": "{group} members",
      "userDescription": "{user} - joined {since} ago",
      "invitationDescription": "invited {since} ago",
      "sendInvite": "Send invite",
      "userAlreadyInGroupTitle": "User is already in the group.",
      "userAlreadyInGroupText": "It is not possible to send an invitation when the user is already a member of the group."
    }
  },
  "fr": {
    "groupMemberModal": {
      "membersModalTitle": "Membres de {group}",
      "userDescription": "{user} - membre depuis {since}",
      "invitationDescription": "invité·e depuis {since}",
      "sendInvite": "Envoyer l'invitation",
      "userAlreadyInGroupTitle": "L'utilisateur est déjà dans le groupe.",
      "userAlreadyInGroupText": "Il n'est pas possible d'envoyer une invitation à un utilisateur déjà présent dans le groupe."
    }
  }
}
</i18n>
