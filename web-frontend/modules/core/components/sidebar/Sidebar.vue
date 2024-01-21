<template>
  <div class="sidebar">
    <div class="sidebar__inner">
      <component
        :is="component"
        v-for="(component, index) in sidebarTopComponents"
        :key="index"
      ></component>
      <a
        ref="userContextAnchor"
        class="sidebar__user"
        @click="
          $refs.userContext.toggle(
            $refs.userContextAnchor,
            'bottom',
            'left',
            isCollapsed ? -4 : -10,
            isCollapsed ? 8 : 16
          )
        "
      >
        <div class="sidebar__user-initials">
          {{ name | nameAbbreviation }}
        </div>
        <div class="sidebar__user-info">
          <div class="sidebar__user-info-top">
            <div class="sidebar__user-name">{{ name }}</div>
            <i class="sidebar__user-icon iconoir-nav-arrow-down"></i>
          </div>
          <div class="sidebar__user-email">{{ email }}</div>
        </div>
      </a>
      <Context
        ref="userContext"
        :overflow-scroll="true"
        :max-height-if-outside-viewport="true"
      >
        <div class="context__menu-title">{{ name }}</div>
        <ul class="context__menu">
          <li class="context__menu-item">
            <a
              class="context__menu-item-link"
              @click=";[$refs.settingsModal.show(), $refs.userContext.hide()]"
            >
              <i class="context__menu-item-icon iconoir-settings"></i>
              {{ $t('sidebar.settings') }}
            </a>
            <SettingsModal ref="settingsModal"></SettingsModal>
          </li>
          <li class="context__menu-item">
            <a
              class="context__menu-item-link"
              :class="{ 'context__menu-item-link--loading': logoffLoading }"
              @click="logoff()"
            >
              <i class="context__menu-item-icon iconoir-log-out"></i>
              {{ $t('sidebar.logoff') }}
            </a>
          </li>
        </ul>
      </Context>
      <div class="sidebar__nav">
        <ul class="tree">
          <li
            class="tree__item"
            :class="{
              active: $route.matched.some(({ name }) => name === 'dashboard'),
            }"
          >
            <div class="tree__action sidebar__action">
              <nuxt-link :to="{ name: 'dashboard' }" class="tree__link">
                <i class="tree__icon iconoir-dashboard-dots"></i>
                <span class="tree__link-text">
                  <span class="sidebar__item-name">{{
                    $t('sidebar.dashboard')
                  }}</span>
                </span>
              </nuxt-link>
            </div>
          </li>
          <component
            :is="component"
            v-for="(component, index) in sidebarMainMenuComponents"
            :key="index"
          ></component>
          <li class="tree__item">
            <div class="tree__action sidebar__action">
              <a class="tree__link" @click="$refs.trashModal.show()">
                <i class="tree__icon iconoir-bin"></i>
                <span class="tree__link-text">
                  <span class="sidebar__item-name">{{
                    $t('sidebar.trash')
                  }}</span>
                </span>
              </a>
              <TrashModal ref="trashModal"></TrashModal>
            </div>
          </li>
          <li v-if="isStaff" class="tree__item">
            <div
              class="tree__action sidebar__action"
              :class="{ 'tree__action--disabled': isAdminPage }"
            >
              <a class="tree__link" @click.prevent="admin()">
                <i class="tree__icon iconoir-settings"></i>
                <span class="tree__link-text">
                  <span class="sidebar__item-name">{{
                    $t('sidebar.admin')
                  }}</span>
                </span>
              </a>
            </div>
            <ul v-show="isAdminPage" class="tree sidebar__tree">
              <SidebarAdminItem
                v-for="adminType in sortedAdminTypes"
                :key="adminType.type"
                :admin-type="adminType"
              >
              </SidebarAdminItem>
            </ul>
          </li>
          <template v-if="hasSelectedWorkspace && !isCollapsed">
            <li class="tree__item margin-top-2">
              <div
                :title="selectedWorkspace.name"
                class="tree__action tree__action--has-options"
                :class="{
                  'tree__action--has-notification':
                    unreadNotificationsInOtherWorkspaces,
                }"
              >
                <a
                  ref="workspaceSelectToggle"
                  class="tree__link tree__link--group"
                  @click="
                    $refs.workspaceSelect.toggle(
                      $refs.workspaceSelectToggle,
                      'bottom',
                      'left',
                      0
                    )
                  "
                >
                  <span class="tree__link-text">
                    <Editable
                      ref="rename"
                      :value="selectedWorkspace.name"
                      @change="renameWorkspace(selectedWorkspace, $event)"
                    ></Editable>
                  </span>
                </a>
                <span
                  v-if="unreadNotificationsInOtherWorkspaces"
                  class="sidebar__unread-notifications-icon"
                ></span>

                <a
                  ref="contextLink"
                  class="tree__options"
                  @click="
                    $refs.context.toggle(
                      $refs.contextLink,
                      'bottom',
                      'right',
                      0
                    )
                  "
                >
                  <i class="baserow-icon-more-vertical"></i>
                </a>

                <WorkspacesContext ref="workspaceSelect"></WorkspacesContext>
                <WorkspaceContext
                  ref="context"
                  :workspace="selectedWorkspace"
                  @rename="enableRename()"
                ></WorkspaceContext>
              </div>
            </li>
            <li class="tree__item">
              <div class="tree__action tree__action--has-counter">
                <a
                  class="tree__link"
                  @click="$refs.notificationPanel.toggle($event.currentTarget)"
                >
                  <i class="tree__icon tree__icon--type iconoir-bell"></i>
                  <span class="tree__link-text">{{
                    $t('sidebar.notifications')
                  }}</span>
                </a>
                <BadgeCounter
                  class="tree__counter"
                  :count="unreadNotificationCount"
                  :limit="10"
                >
                </BadgeCounter>
              </div>
              <NotificationPanel ref="notificationPanel" />
            </li>
            <li
              v-if="
                $hasPermission(
                  'workspace.create_invitation',
                  selectedWorkspace,
                  selectedWorkspace.id
                )
              "
              class="tree__item"
            >
              <div class="tree__action">
                <a class="tree__link" @click="$refs.inviteModal.show()">
                  <i class="tree__icon tree__icon--type iconoir-add-user"></i>
                  <span class="tree__link-text">{{
                    $t('sidebar.inviteOthers')
                  }}</span>
                </a>
              </div>
              <WorkspaceMemberInviteModal
                ref="inviteModal"
                :workspace="selectedWorkspace"
                @invite-submitted="handleInvite"
              />
            </li>
            <nuxt-link
              v-if="
                $hasPermission(
                  'workspace.list_workspace_users',
                  selectedWorkspace,
                  selectedWorkspace.id
                )
              "
              v-slot="{ href, navigate, isExactActive }"
              :to="{
                name: 'settings-members',
                params: {
                  workspaceId: selectedWorkspace.id,
                },
              }"
            >
              <li class="tree__item" :class="{ active: isExactActive }">
                <div class="tree__action">
                  <a :href="href" class="tree__link" @click="navigate">
                    <i
                      class="tree__icon tree__icon--type iconoir-community"
                    ></i>
                    <span class="tree__link-text">{{
                      $t('sidebar.members')
                    }}</span>
                  </a>
                </div>
              </li>
            </nuxt-link>
            <component
              :is="component"
              v-for="(component, index) in sidebarWorkspaceComponents"
              :key="'sidebarWorkspaceComponents' + index"
              :workspace="selectedWorkspace"
            ></component>
            <ul class="tree">
              <component
                :is="getApplicationComponent(application)"
                v-for="application in applications"
                :key="application.id"
                v-sortable="{
                  id: application.id,
                  update: orderApplications,
                  handle: '[data-sortable-handle]',
                  marginTop: -1.5,
                  enabled: $hasPermission(
                    'workspace.order_applications',
                    selectedWorkspace,
                    selectedWorkspace.id
                  ),
                }"
                :application="application"
                :workspace="selectedWorkspace"
              ></component>
            </ul>
            <ul v-if="pendingJobs.length" class="tree">
              <component
                :is="getPendingJobComponent(job)"
                v-for="job in pendingJobs"
                :key="job.id"
                :job="job"
              >
              </component>
            </ul>
            <li class="sidebar__new-wrapper">
              <a
                v-if="
                  $hasPermission(
                    'workspace.create_application',
                    selectedWorkspace,
                    selectedWorkspace.id
                  )
                "
                ref="createApplicationContextLink"
                class="sidebar__new"
                @click="
                  $refs.createApplicationContext.toggle(
                    $refs.createApplicationContextLink
                  )
                "
              >
                <i class="sidebar__new-icon iconoir-plus"></i>
                {{ $t('action.createNew') }}
              </a>
            </li>
            <CreateApplicationContext
              ref="createApplicationContext"
              :workspace="selectedWorkspace"
            ></CreateApplicationContext>
          </template>
          <template v-else-if="!hasSelectedWorkspace && !isCollapsed">
            <li v-if="workspaces.length === 0" class="tree_item margin-top-2">
              <p>{{ $t('sidebar.errorNoWorkspace') }}</p>
            </li>
            <li
              v-for="(workspace, index) in workspaces"
              :key="workspace.id"
              class="tree__item"
              :class="{
                'margin-top-2': index === 0,
                'tree__item--loading': workspace._.additionalLoading,
              }"
            >
              <div
                class="tree__action tree__action--has-right-icon tree__action--has-notification"
              >
                <a
                  class="tree__link tree__link--group"
                  @click="$store.dispatch('workspace/select', workspace)"
                  ><span class="tree__link-text">{{ workspace.name }}</span></a
                >
                <span
                  v-if="hasUnreadNotifications(workspace.id)"
                  class="sidebar__unread-notifications-icon"
                ></span>
                <span class="tree__right-icon">
                  <i class="iconoir-arrow-right"></i>
                </span>
              </div>
            </li>
            <li class="sidebar__new-wrapper">
              <a
                v-if="$hasPermission('create_workspace')"
                class="sidebar__new"
                @click="$refs.createWorkspaceModal.show()"
              >
                <i class="iconoir-plus"></i>
                {{ $t('sidebar.createWorkspace') }}
              </a>
            </li>
            <CreateWorkspaceModal
              ref="createWorkspaceModal"
            ></CreateWorkspaceModal>
          </template>
        </ul>
      </div>
      <div class="sidebar__foot sidebar__foot--with-undo-redo">
        <div class="sidebar__logo">
          <BaserowLogo />
        </div>
        <div class="sidebar__foot-links">
          <a
            class="sidebar__foot-link"
            :class="{
              'sidebar__foot-link--loading': undoLoading,
            }"
            @click="undo(false)"
          >
            <i class="sidebar__foot-link-icon iconoir-undo"></i>
          </a>
          <a
            class="sidebar__foot-link"
            :class="{
              'sidebar__foot-link--loading': redoLoading,
            }"
            @click="redo(false)"
          >
            <i class="sidebar__foot-link-icon iconoir-redo"></i>
          </a>
          <a
            class="sidebar__foot-link"
            @click="$store.dispatch('sidebar/toggleCollapsed')"
          >
            <i
              class="sidebar__foot-link-icon"
              :class="{
                'iconoir-fast-arrow-right': isCollapsed,
                'iconoir-fast-arrow-left': !isCollapsed,
              }"
            ></i>
          </a>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapGetters, mapState } from 'vuex'

import { notifyIf } from '@baserow/modules/core/utils/error'
import SettingsModal from '@baserow/modules/core/components/settings/SettingsModal'
import SidebarAdminItem from '@baserow/modules/core/components/sidebar/SidebarAdminItem'
import SidebarApplication from '@baserow/modules/core/components/sidebar/SidebarApplication'
import CreateApplicationContext from '@baserow/modules/core/components/application/CreateApplicationContext'
import WorkspacesContext from '@baserow/modules/core/components/workspace/WorkspacesContext'
import WorkspaceContext from '@baserow/modules/core/components/workspace/WorkspaceContext'
import CreateWorkspaceModal from '@baserow/modules/core/components/workspace/CreateWorkspaceModal'
import TrashModal from '@baserow/modules/core/components/trash/TrashModal'
import editWorkspace from '@baserow/modules/core/mixins/editWorkspace'
import undoRedo from '@baserow/modules/core/mixins/undoRedo'
import BaserowLogo from '@baserow/modules/core/components/BaserowLogo'
import WorkspaceMemberInviteModal from '@baserow/modules/core/components/workspace/WorkspaceMemberInviteModal'
import { logoutAndRedirectToLogin } from '@baserow/modules/core/utils/auth'
import NotificationPanel from '@baserow/modules/core/components/NotificationPanel'
import BadgeCounter from '@baserow/modules/core/components/BadgeCounter'

export default {
  name: 'Sidebar',
  components: {
    BaserowLogo,
    SettingsModal,
    CreateApplicationContext,
    SidebarAdminItem,
    SidebarApplication,
    WorkspacesContext,
    WorkspaceContext,
    CreateWorkspaceModal,
    TrashModal,
    WorkspaceMemberInviteModal,
    NotificationPanel,
    BadgeCounter,
  },
  mixins: [editWorkspace, undoRedo],
  data() {
    return {
      logoffLoading: false,
    }
  },
  computed: {
    /**
     * Because all the applications that belong to the user are in the store we will
     * filter on the selected workspace here.
     */
    applications() {
      return this.$store.getters['application/getAllOfWorkspace'](
        this.selectedWorkspace
      ).sort((a, b) => a.order - b.order)
    },
    adminTypes() {
      return this.$registry.getAll('admin')
    },
    sortedAdminTypes() {
      return Object.values(this.adminTypes)
        .slice()
        .sort((a, b) => a.getOrder() - b.getOrder())
    },
    sidebarTopComponents() {
      return Object.values(this.$registry.getAll('plugin'))
        .map((plugin) => plugin.getSidebarTopComponent())
        .filter((component) => component !== null)
    },
    sidebarMainMenuComponents() {
      return Object.values(this.$registry.getAll('plugin'))
        .map((plugin) => plugin.getSidebarMainMenuComponent())
        .filter((component) => component !== null)
    },
    sidebarWorkspaceComponents() {
      return Object.values(this.$registry.getAll('plugin'))
        .flatMap((plugin) =>
          plugin.getSidebarWorkspaceComponents(this.selectedWorkspace)
        )
        .filter((component) => component !== null)
    },
    pendingJobs() {
      return this.$store.getters['job/getAll'].filter((job) =>
        this.$registry
          .get('job', job.type)
          .isJobPartOfWorkspace(job, this.selectedWorkspace)
      )
    },
    /**
     * Indicates whether the current user is visiting an admin page.
     */
    isAdminPage() {
      return Object.values(this.adminTypes).some((adminType) => {
        return this.$route.matched.some(
          ({ name }) => name === adminType.routeName
        )
      })
    },
    ...mapState({
      workspaces: (state) => state.workspace.items,
      selectedWorkspace: (state) => state.workspace.selected,
    }),
    ...mapGetters({
      isStaff: 'auth/isStaff',
      name: 'auth/getName',
      email: 'auth/getUsername',
      hasSelectedWorkspace: 'workspace/hasSelected',
      isCollapsed: 'sidebar/isCollapsed',
      unreadNotificationCount: 'notification/getUnreadCount',
      unreadNotificationsInOtherWorkspaces:
        'notification/anyOtherWorkspaceWithUnread',
    }),
  },
  methods: {
    hasUnreadNotifications(workspaceId) {
      return this.$store.getters['notification/workspaceHasUnread'](workspaceId)
    },
    getApplicationComponent(application) {
      return this.$registry
        .get('application', application.type)
        .getSidebarComponent()
    },
    getPendingJobComponent(job) {
      return this.$registry.get('job', job.type).getSidebarComponent()
    },
    logoff() {
      this.logoffLoading = true
      logoutAndRedirectToLogin(
        this.$nuxt.$router,
        this.$store,
        false,
        false,
        true
      )
    },
    /**
     * Called when the user clicks on the admin menu. Because there isn't an
     * admin page it will navigate to the route of the first registered admin
     * type.
     */
    admin() {
      // If the user is already on an admin page we don't have to do anything because
      // the link is disabled.
      if (this.isAdminPage) {
        return
      }

      // We only want to autoselect the first active admin type because the other ones
      // can't be selected.
      const activated = this.sortedAdminTypes.filter((adminType) => {
        return !this.$registry.get('admin', adminType.type).isDeactivated()
      })

      if (activated.length > 0) {
        this.$nuxt.$router.push({ name: activated[0].routeName })
      }
    },
    async orderApplications(order, oldOrder) {
      try {
        await this.$store.dispatch('application/order', {
          workspace: this.selectedWorkspace,
          order,
          oldOrder,
        })
      } catch (error) {
        notifyIf(error, 'application')
      }
    },
    handleInvite(event) {
      if (this.$route.name !== 'settings-invites') {
        this.$router.push({
          name: 'settings-invites',
          params: {
            workspaceId: this.selectedWorkspace.id,
          },
        })
      }
    },
  },
}
</script>
