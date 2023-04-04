<template>
  <div class="layout__col-2-scroll layout__col-2-scroll--white-background">
    <div class="dashboard">
      <DashboardHelp></DashboardHelp>
      <WorkspaceInvitation
        v-for="invitation in workspaceInvitations"
        :key="'invitation-' + invitation.id"
        :invitation="invitation"
        @remove="removeInvitation($event)"
      ></WorkspaceInvitation>
      <div class="dashboard__container">
        <div class="dashboard__sidebar">
          <DashboardSidebar
            :workspaces="sortedWorkspaces"
            @workspace-selected="scrollToWorkspace"
            @create-workspace-clicked="$refs.createWorkspaceModal.show()"
          ></DashboardSidebar>
        </div>
        <div class="dashboard__content">
          <DashboardNoWorkspaces
            v-if="workspaces.length === 0"
            @create-clicked="$refs.createWorkspaceModal.show()"
          ></DashboardNoWorkspaces>
          <template v-else>
            <DashboardWorkspace
              v-for="workspace in sortedWorkspaces"
              :ref="'workspace-' + workspace.id"
              :key="workspace.id"
              :workspace="workspace"
              :component-arguments="workspaceComponentArguments"
            ></DashboardWorkspace>
            <div>
              <a
                v-if="$hasPermission('create_workspace')"
                class="dashboard__create-link"
                @click="$refs.createWorkspaceModal.show()"
              >
                <i class="fas fa-plus"></i>
                {{ $t('dashboard.createWorkspace') }}
              </a>
            </div>
          </template>
        </div>
      </div>
    </div>
    <CreateWorkspaceModal ref="createWorkspaceModal"></CreateWorkspaceModal>
  </div>
</template>

<script>
import { mapState, mapGetters } from 'vuex'

import CreateWorkspaceModal from '@baserow/modules/core/components/workspace/CreateWorkspaceModal'
import WorkspaceInvitation from '@baserow/modules/core/components/workspace/WorkspaceInvitation'
import DashboardWorkspace from '@baserow/modules/core/components/dashboard/DashboardWorkspace'
import DashboardHelp from '@baserow/modules/core/components/dashboard/DashboardHelp'
import DashboardNoWorkspaces from '@baserow/modules/core/components/dashboard/DashboardNoWorkspaces'
import DashboardSidebar from '@baserow/modules/core/components/dashboard/DashboardSidebar'
import AuthService from '@baserow/modules/core/services/auth'

export default {
  components: {
    DashboardHelp,
    DashboardNoWorkspaces,
    DashboardSidebar,
    CreateWorkspaceModal,
    DashboardWorkspace,
    WorkspaceInvitation,
  },
  layout: 'app',
  /**
   * Fetches the data that must be shown on the dashboard, this could for example be
   * pending workspace invitations.
   */
  async asyncData(context) {
    const { error, app } = context
    try {
      const { data } = await AuthService(app.$client).dashboard()
      let asyncData = {
        workspaceInvitations: data.workspace_invitations,
        workspaceComponentArguments: {},
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
      sortedWorkspaces: 'workspace/getAllSorted',
    }),
    ...mapState({
      user: (state) => state.auth.user,
      workspaces: (state) => state.workspace.items,
      applications: (state) => state.application.items,
    }),
  },
  methods: {
    /**
     * When a workspace invitation has been rejected or accepted, it can be removed from the
     * list because in both situations the invitation itself is deleted.
     */
    removeInvitation(invitation) {
      const index = this.workspaceInvitations.findIndex(
        (i) => i.id === invitation.id
      )
      this.workspaceInvitations.splice(index, 1)
    },
    /**
     * Make sure that the selected workspace is visible.
     */
    scrollToWorkspace(workspace) {
      const ref = this.$refs['workspace-' + workspace.id]
      if (ref) {
        const element = ref[0].$el
        element.scrollIntoView({ behavior: 'smooth' })
      }
    },
  },
}
</script>
