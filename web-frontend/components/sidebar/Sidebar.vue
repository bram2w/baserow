<template>
  <div>
    <div v-if="hasSelectedGroup">
      <div class="sidebar-group-title">{{ selectedGroup.name }}</div>
      <ul class="tree">
        <SidebarApplication
          v-for="application in applications"
          :key="application.id"
          :application="application"
        ></SidebarApplication>
      </ul>
      <a
        ref="createApplicationContextLink"
        class="sidebar-new"
        @click="
          $refs.createApplicationContext.toggle(
            $refs.createApplicationContextLink
          )
        "
      >
        <i class="fas fa-plus"></i>
        Create new
      </a>
      <CreateApplicationContext
        ref="createApplicationContext"
      ></CreateApplicationContext>
    </div>
  </div>
</template>

<script>
import { mapGetters, mapState } from 'vuex'

import SidebarApplication from '@/components/sidebar/SidebarApplication'
import CreateApplicationContext from '@/components/sidebar/CreateApplicationContext'

export default {
  name: 'Sidebar',
  components: {
    CreateApplicationContext,
    SidebarApplication
  },
  computed: {
    ...mapState({
      applications: state => state.application.items,
      selectedGroup: state => state.group.selected
    }),
    ...mapGetters({
      isLoading: 'application/isLoading',
      hasSelectedGroup: 'group/hasSelected'
    })
  }
}
</script>
