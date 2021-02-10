<template>
  <div class="layout__col-2-scroll">
    <div
      class="alert alert--simple alert--warning alert--has-icon dashboard__alert"
    >
      <div class="alert__icon">
        <i class="fas fa-exclamation"></i>
      </div>
      <div class="alert__title">We need your help!</div>
      <p class="alert__content">
        Do you like Baserow and where the product is headed? Do you want to see
        new features sooner? By becoming a sponsor you will allow us to spend
        more time on the development of Baserow which means you will get new
        features faster. Your help is much appreciated.
      </p>
      <a
        href="https://github.com/sponsors/bram2w"
        target="_blank"
        class="button button--primary dashboard__alert-button"
      >
        Become a GitHub sponsor
        <i class="fa fa-heart"></i>
      </a>
    </div>
    <GroupInvitation
      v-for="invitation in groupInvitations"
      :key="'invitation-' + invitation.id"
      :invitation="invitation"
      @remove="removeInvitation($event)"
    ></GroupInvitation>
    <div v-if="groups.length === 0" class="placeholder">
      <div class="placeholder__icon">
        <i class="fas fa-layer-group"></i>
      </div>
      <h1 class="placeholder__title">No groups found</h1>
      <p class="placeholder__content">
        You aren’t a member of any group. Applications like databases belong to
        a group, so in order to create them you need to create a group.
      </p>
      <div class="placeholder__action">
        <a class="button button--large" @click="$refs.createGroupModal.show()">
          <i class="fas fa-plus"></i>
          Create group
        </a>
      </div>
    </div>
    <div v-if="groups.length > 0" class="dashboard">
      <DashboardGroup
        v-for="group in groups"
        :key="group.id"
        :group="group"
      ></DashboardGroup>
      <div>
        <a class="button button--large" @click="$refs.createGroupModal.show()">
          <i class="fas fa-plus"></i>
          Create group
        </a>
      </div>
    </div>
    <CreateGroupModal ref="createGroupModal"></CreateGroupModal>
  </div>
</template>

<script>
import { mapState } from 'vuex'

import CreateGroupModal from '@baserow/modules/core/components/group/CreateGroupModal'
import DashboardGroup from '@baserow/modules/core/components/group/DashboardGroup'
import GroupInvitation from '@baserow/modules/core/components/group/GroupInvitation'
import AuthService from '@baserow/modules/core/services/auth'

export default {
  components: { CreateGroupModal, DashboardGroup, GroupInvitation },
  layout: 'app',
  /**
   * Fetches the data that must be shown on the dashboard, this could for example be
   * pending group invitations.
   */
  async asyncData({ error, app }) {
    try {
      const { data } = await AuthService(app.$client).dashboard()
      return { groupInvitations: data.group_invitations }
    } catch (e) {
      return error({ statusCode: 400, message: 'Error loading dashboard.' })
    }
  },
  head() {
    return {
      title: 'Dashboard',
    }
  },
  computed: {
    ...mapState({
      user: (state) => state.auth.user,
      groups: (state) => state.group.items,
      applications: (state) => state.application.items,
    }),
  },
  methods: {
    /**
     * When a group invation has been rejected or accepted, it can be removed from the
     * list because in both situations the invitation itself is deleted.
     */
    removeInvitation(invitation) {
      const index = this.groupInvitations.findIndex(
        (i) => i.id === invitation.id
      )
      this.groupInvitations.splice(index, 1)
    },
  },
}
</script>
