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

import SidebarApplication from '@baserow/modules/core/components/sidebar/SidebarApplication'
import CreateApplicationContext from '@baserow/modules/core/components/application/CreateApplicationContext'

export default {
  name: 'Sidebar',
  components: {
    CreateApplicationContext,
    SidebarApplication,
  },
  computed: {
    /**
     * Because all the applications that belong to the user are in the store we will
     * filter on the selected group here.
     */
    applications() {
      return this.allApplications.filter(
        (application) => application.group.id === this.selectedGroup.id
      )
    },
    ...mapState({
      allApplications: (state) => state.application.items,
      selectedGroup: (state) => state.group.selected,
    }),
    ...mapGetters({
      isLoading: 'application/isLoading',
      hasSelectedGroup: 'group/hasSelected',
    }),
  },
}
</script>
