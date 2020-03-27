<template>
  <div>
    <Notifications></Notifications>
    <div :class="{ 'layout-collapsed': isCollapsed }" class="layout">
      <div class="layout-col-1 menu">
        <ul class="menu-items">
          <li class="menu-item">
            <nuxt-link :to="{ name: 'dashboard' }" class="menu-link">
              <i class="fas fa-tachometer-alt"></i>
              <span class="menu-link-text">Dashboard</span>
            </nuxt-link>
          </li>
          <li class="menu-item">
            <a
              ref="groupSelectToggle"
              class="menu-link"
              @click="$refs.groupSelect.toggle($refs.groupSelectToggle)"
            >
              <i class="fas fa-layer-group"></i>
              <span class="menu-link-text">Groups</span>
            </a>
            <GroupsContext ref="groupSelect"></GroupsContext>
          </li>
        </ul>
        <ul class="menu-items">
          <li class="menu-item layout-uncollapse">
            <a class="menu-link" @click="toggleCollapsed()">
              <i class="menu-item-icon fas fa-angle-double-right"></i>
              <span class="menu-link-text">Uncollapse</span>
            </a>
          </li>
          <li class="menu-item">
            <a
              class="menu-link menu-user-item"
              @click="$refs.userContext.toggle($event.target)"
            >
              {{ nameAbbreviation }}
              <span class="menu-link-text">{{ name }}</span>
            </a>
            <Context ref="userContext">
              <div class="context-menu-title">{{ name }}</div>
              <ul class="context-menu">
                <li>
                  <a @click="logoff()">
                    <i class="context-menu-icon fas fa-fw fa-sign-out-alt"></i>
                    Logoff
                  </a>
                </li>
              </ul>
            </Context>
          </li>
        </ul>
      </div>
      <div class="layout-col-2 sidebar">
        <div class="sidebar-content-wrapper">
          <nav class="sidebar-content">
            <div class="sidebar-title">
              <img src="@baserow/modules/core/static/img/logo.svg" alt="" />
            </div>
            <Sidebar></Sidebar>
          </nav>
        </div>
        <div class="sidebar-footer">
          <a class="sidebar-collapse" @click="toggleCollapsed()">
            <i class="fas fa-angle-double-left"></i>
            Collapse sidebar
          </a>
        </div>
      </div>
      <div class="layout-col-3">
        <nuxt />
      </div>
    </div>
  </div>
</template>

<script>
import { mapActions, mapGetters } from 'vuex'

import Notifications from '@baserow/modules/core/components/notifications/Notifications'
import GroupsContext from '@baserow/modules/core/components/group/GroupsContext'
import Sidebar from '@baserow/modules/core/components/sidebar/Sidebar'

export default {
  // Application pages are pages that have the edit sidebar on the left side which
  // contains the groups and applications. In order to be able to fetch them the user
  // must be authenticated. And in order to show them we must fetch all the groups and
  // applications.
  middleware: ['authenticated', 'groupsAndApplications'],
  components: {
    GroupsContext,
    Notifications,
    Sidebar
  },
  computed: {
    ...mapGetters({
      isCollapsed: 'sidebar/isCollapsed',
      name: 'auth/getName',
      nameAbbreviation: 'auth/getNameAbbreviation'
    })
  },
  methods: {
    logoff() {
      this.$store.dispatch('auth/logoff')
      this.$nuxt.$router.push({ name: 'login' })
    },
    ...mapActions({
      toggleCollapsed: 'sidebar/toggleCollapsed'
    })
  }
}
</script>
