<template>
  <div>
    <Notifications></Notifications>
    <SettingsModal ref="settingsModal"></SettingsModal>
    <div :class="{ 'layout--collapsed': isCollapsed }" class="layout">
      <div class="layout__col-1 menu">
        <ul class="menu__items">
          <li class="menu__item">
            <nuxt-link :to="{ name: 'dashboard' }" class="menu__link">
              <i class="fas fa-tachometer-alt"></i>
              <span class="menu__link-text">Dashboard</span>
            </nuxt-link>
          </li>
          <li class="menu__item">
            <a
              ref="groupSelectToggle"
              class="menu__link"
              @click="$refs.groupSelect.toggle($refs.groupSelectToggle)"
            >
              <i class="fas fa-layer-group"></i>
              <span class="menu__link-text">Groups</span>
            </a>
            <GroupsContext ref="groupSelect"></GroupsContext>
          </li>
        </ul>
        <ul class="menu__items">
          <li class="menu__item layout__uncollapse">
            <a class="menu__link" @click="toggleCollapsed()">
              <i class="fas fa-angle-double-right"></i>
              <span class="menu__link-text">Uncollapse</span>
            </a>
          </li>
          <li class="menu__item">
            <a
              class="menu__link menu__user-item"
              @click="$refs.userContext.toggle($event.target)"
            >
              {{ nameAbbreviation }}
              <span class="menu__link-text">{{ name }}</span>
            </a>
            <Context ref="userContext">
              <div class="context__menu-title">{{ name }}</div>
              <ul class="context__menu">
                <li>
                  <a
                    @click="
                      ;[
                        $refs.settingsModal.show('password'),
                        $refs.userContext.hide(),
                      ]
                    "
                  >
                    <i class="context__menu-icon fas fa-fw fa-cogs"></i>
                    Settings
                  </a>
                </li>
                <li>
                  <a @click="logoff()">
                    <i class="context__menu-icon fas fa-fw fa-sign-out-alt"></i>
                    Logoff
                  </a>
                </li>
              </ul>
            </Context>
          </li>
        </ul>
      </div>
      <div class="layout__col-2 sidebar">
        <div class="sidebar__content-wrapper">
          <nav class="sidebar__content">
            <div class="sidebar__title">
              <img src="@baserow/modules/core/static/img/logo.svg" alt="" />
            </div>
            <Sidebar></Sidebar>
          </nav>
        </div>
        <div class="sidebar__footer">
          <a class="sidebar__collapse" @click="toggleCollapsed()">
            <i class="fas fa-angle-double-left"></i>
            Collapse sidebar
          </a>
        </div>
      </div>
      <div class="layout__col-3">
        <nuxt />
      </div>
    </div>
  </div>
</template>

<script>
import { mapActions, mapGetters } from 'vuex'

import SettingsModal from '@baserow/modules/core/components/settings/SettingsModal'
import Notifications from '@baserow/modules/core/components/notifications/Notifications'
import GroupsContext from '@baserow/modules/core/components/group/GroupsContext'
import Sidebar from '@baserow/modules/core/components/sidebar/Sidebar'

export default {
  components: {
    SettingsModal,
    GroupsContext,
    Notifications,
    Sidebar,
  },
  // Application pages are pages that have the edit sidebar on the left side which
  // contains the groups and applications. In order to be able to fetch them the user
  // must be authenticated. And in order to show them we must fetch all the groups and
  // applications.
  middleware: ['authenticated', 'groupsAndApplications'],
  computed: {
    ...mapGetters({
      isCollapsed: 'sidebar/isCollapsed',
      name: 'auth/getName',
      nameAbbreviation: 'auth/getNameAbbreviation',
    }),
  },
  mounted() {
    // Connect to the web socket so we can start receiving real time updates.
    this.$realtime.connect()
  },
  beforeDestroy() {
    this.$realtime.disconnect()
  },
  methods: {
    logoff() {
      this.$store.dispatch('auth/logoff')
      this.$nuxt.$router.push({ name: 'login' })
    },
    ...mapActions({
      toggleCollapsed: 'sidebar/toggleCollapsed',
    }),
  },
}
</script>
