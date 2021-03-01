<template>
  <div>
    <Notifications></Notifications>
    <div :class="{ 'layout--collapsed': isCollapsed }" class="layout">
      <div class="layout__col-1">
        <Sidebar></Sidebar>
      </div>
      <div class="layout__col-2">
        <nuxt />
      </div>
    </div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'

import Notifications from '@baserow/modules/core/components/notifications/Notifications'
import Sidebar from '@baserow/modules/core/components/sidebar/Sidebar'

export default {
  components: {
    Notifications,
    Sidebar,
  },
  middleware: ['settings', 'authenticated', 'groupsAndApplications'],
  computed: {
    ...mapGetters({
      isCollapsed: 'sidebar/isCollapsed',
    }),
  },
  mounted() {
    // Connect to the web socket so we can start receiving real time updates.
    this.$realtime.connect()
  },
  beforeDestroy() {
    this.$realtime.disconnect()
  },
}
</script>
