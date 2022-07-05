<template>
  <div class="layout__col-2-scroll layout__col-2-scroll--white-background">
    <div class="dashboard">
      <DashboardHelp></DashboardHelp>
      <GroupInvitation
        v-for="invitation in groupInvitations"
        :key="'invitation-' + invitation.id"
        :invitation="invitation"
        @remove="removeInvitation($event)"
      ></GroupInvitation>
      <div class="dashboard__container">
        <div class="dashboard__sidebar">
          <DashboardSidebar
            :groups="sortedGroups"
            @group-selected="scrollToGroup"
            @create-group-clicked="$refs.createGroupModal.show()"
          ></DashboardSidebar>
        </div>
        <div class="dashboard__content">
          <DashboardNoGroups
            v-if="groups.length === 0"
            @create-clicked="$refs.createGroupModal.show()"
          ></DashboardNoGroups>
          <template v-else>
            <DashboardGroup
              v-for="group in sortedGroups"
              :ref="'group-' + group.id"
              :key="group.id"
              :group="group"
              :component-arguments="groupComponentArguments"
            ></DashboardGroup>
            <div>
              <a
                class="dashboard__create-link"
                @click="$refs.createGroupModal.show()"
              >
                <i class="fas fa-plus"></i>
                {{ $t('dashboard.createGroup') }}
              </a>
            </div>
          </template>
        </div>
      </div>
    </div>
    <CreateGroupModal ref="createGroupModal"></CreateGroupModal>
  </div>
</template>

<script>
import { mapState, mapGetters } from 'vuex'

import CreateGroupModal from '@baserow/modules/core/components/group/CreateGroupModal'
import GroupInvitation from '@baserow/modules/core/components/group/GroupInvitation'
import DashboardGroup from '@baserow/modules/core/components/dashboard/DashboardGroup'
import DashboardHelp from '@baserow/modules/core/components/dashboard/DashboardHelp'
import DashboardNoGroups from '@baserow/modules/core/components/dashboard/DashboardNoGroups'
import DashboardSidebar from '@baserow/modules/core/components/dashboard/DashboardSidebar'
import AuthService from '@baserow/modules/core/services/auth'

export default {
  components: {
    DashboardHelp,
    DashboardNoGroups,
    DashboardSidebar,
    CreateGroupModal,
    DashboardGroup,
    GroupInvitation,
  },
  layout: 'app',
  /**
   * Fetches the data that must be shown on the dashboard, this could for example be
   * pending group invitations.
   */
  async asyncData(context) {
    const { error, app } = context
    try {
      const { data } = await AuthService(app.$client).dashboard()
      let asyncData = {
        groupInvitations: data.group_invitations,
        groupComponentArguments: {},
      }
      // Loop over all the plugin and call the `fetchAsyncDashboardData` because there
      // might be plugins that extend the dashboard and we want to fetch that async data
      // here.
      const plugins = Object.values(app.$registry.getAll('plugin'))
      for (let i = 0; i < plugins.length; i++) {
        asyncData = await plugins[i].fetchAsyncDashboardData(context, asyncData)
      }
      return asyncData
    } catch (e) {
      return error({ statusCode: 400, message: 'Error loading dashboard.' })
    }
  },
  head() {
    return {
      title: this.$t('dashboard.title'),
    }
  },
  computed: {
    ...mapGetters({
      sortedGroups: 'group/getAllSorted',
    }),
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
    /**
     * Make sure that the selected group is visible.
     */
    scrollToGroup(group) {
      const ref = this.$refs['group-' + group.id]
      if (ref) {
        const element = ref[0].$el
        element.scrollIntoView({ behavior: 'smooth' })
      }
    },
  },
}
</script>
