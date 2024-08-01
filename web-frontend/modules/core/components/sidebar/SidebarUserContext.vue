<template>
  <Context :max-height-if-outside-viewport="true" class="select">
    <ul
      ref="dropdown"
      v-auto-overflow-scroll
      class="select__items select__items--no-max-height dashboard__user-workspaces"
    >
      <li
        v-for="workspace in workspaces"
        :key="workspace.id"
        class="select__item"
        :class="{
          'select__item--loading':
            workspace._.loading || workspace._.additionalLoading,
          active: workspace.id === selectedWorkspace.id,
        }"
      >
        <i
          v-if="workspace.id === selectedWorkspace.id"
          class="sidebar__workspace-active-icon iconoir-check"
        ></i>
        <a class="select__item-link" @click="selectWorkspace(workspace)">
          <div class="select__item-name">
            <Avatar
              class="dashboard__user-workspace-avatar"
              :initials="workspace.name | nameAbbreviation"
            ></Avatar>
            {{ workspace.name }}
            <span
              v-if="hasUnreadNotifications(workspace.id)"
              class="sidebar__unread-notifications-icon"
            ></span>
          </div>
        </a>
      </li>
      <li class="select__item">
        <a class="select__item-link" @click="$refs.createWorkspaceModal.show()">
          <div class="select__item-name">
            <ButtonIcon
              tag="a"
              size="small"
              type="secondary"
              icon="iconoir-plus"
              style="pointer-events: none"
            />
            <span>{{ $t('sidebar.addNewWorkspace') }}</span>
          </div>
        </a>
      </li>
    </ul>
    <div class="sidebar__user">
      <div class="sidebar__user-info">
        <span class="sidebar__user-email">
          {{ email }}
        </span>

        <component
          :is="component"
          v-for="(component, index) in highestLicenceTypeBadge"
          :key="index"
          class="sidebar__user-license"
        ></component>
      </div>

      <ul class="context__menu margin-bottom-0">
        <li v-if="isStaff" class="context__menu-item">
          <a class="context__menu-item-link" @click="admin">
            <i class="context__menu-item-icon iconoir-settings"></i>
            {{ $t('sidebar.adminTools') }}
          </a>
        </li>

        <li class="context__menu-item">
          <a
            class="context__menu-item-link"
            @click="$refs.settingsModal.show()"
          >
            <i class="context__menu-item-icon iconoir-user-circle"></i>
            {{ $t('sidebar.settings') }}
          </a>
          <SettingsModal ref="settingsModal"></SettingsModal>
        </li>

        <component
          :is="component"
          v-for="(component, index) in sidebarUserContextComponents"
          :key="'sidebarUserContextComponent' + index"
          @hide="hide()"
        ></component>

        <li
          class="context__menu-item context__menu-item--with-separator margin-bottom-0"
        >
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
    </div>
    <CreateWorkspaceModal ref="createWorkspaceModal"></CreateWorkspaceModal>
  </Context>
</template>

<script>
import { mapGetters } from 'vuex'

import { logoutAndRedirectToLogin } from '@baserow/modules/core/utils/auth'
import context from '@baserow/modules/core/mixins/context'
import SettingsModal from '@baserow/modules/core/components/settings/SettingsModal'
import CreateWorkspaceModal from '@baserow/modules/core/components/workspace/CreateWorkspaceModal'

export default {
  name: 'SidebarUserContext',
  components: { SettingsModal, CreateWorkspaceModal },
  mixins: [context],
  props: {
    workspaces: {
      type: Array,
      required: true,
    },
    selectedWorkspace: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      logoffLoading: false,
    }
  },
  computed: {
    highestLicenceTypeBadge() {
      return Object.values(this.$registry.getAll('plugin'))
        .map((plugin) => plugin.getHighestLicenseTypeBadge())
        .filter((component) => component !== null)
    },
    adminTypes() {
      return this.$registry.getAll('admin')
    },
    sortedAdminTypes() {
      return Object.values(this.adminTypes)
        .slice()
        .sort((a, b) => a.getOrder() - b.getOrder())
    },
    sidebarUserContextComponents() {
      return Object.values(this.$registry.getAll('plugin'))
        .flatMap((plugin) =>
          plugin.getUserContextComponents(this.selectedWorkspace)
        )
        .filter((component) => component !== null)
    },
    ...mapGetters({
      isStaff: 'auth/isStaff',
      name: 'auth/getName',
      email: 'auth/getUsername',
    }),
  },
  methods: {
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
    async admin() {
      this.$emit('toggle-admin', true)
      this.hide()
      const activatedAdminTypes = this.sortedAdminTypes.filter(
        (adminType) => !adminType.isDeactivated()
      )
      try {
        await this.$router.push({ name: activatedAdminTypes[0].routeName })
      } catch {}
    },
    hasUnreadNotifications(workspaceId) {
      return this.$store.getters['notification/workspaceHasUnread'](workspaceId)
    },
    async selectWorkspace(workspace) {
      if (workspace._.selected) {
        return
      }
      await this.$store.dispatch('workspace/select', workspace)
      await this.$router.push({
        name: 'workspace',
        params: { workspaceId: workspace.id },
      })
      this.hide()
    },
  },
}
</script>
