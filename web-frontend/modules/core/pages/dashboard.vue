<template>
  <div>
    <h1>Welcome {{ user }}</h1>
    <p>
      {{ groups }}
      <br /><br />
      {{ selectedGroup }}
      <br /><br />
      {{ applications }}
      <br /><br />
      {{ groupApplications }}
      <br /><br />
      <nuxt-link
        :to="{ name: 'database-table', params: { databaseId: 1, tableId: 5 } }"
      >
        <i class="fas fa-arrow-right"></i>
        Database 1 table 5
      </nuxt-link>
      <br /><br />
      <nuxt-link
        :to="{
          name: 'database-table',
          params: { databaseId: 1, tableId: 5, viewId: 5 },
        }"
      >
        <i class="fas fa-arrow-right"></i>
        Database 1 table 5 view 5
      </nuxt-link>
    </p>
  </div>
</template>

<script>
import { mapState } from 'vuex'

export default {
  layout: 'app',
  computed: {
    ...mapState({
      user: (state) => state.auth.user,
      groups: (state) => state.group.items,
      selectedGroup: (state) => state.group.selected,
      applications: (state) => state.application.applications,
      groupApplications: (state) => state.application.items,
    }),
  },
  head() {
    return {
      title: 'Dashboard',
    }
  },
}
</script>
