<template>
  <div class="notifications">
    <Notification
      v-for="notification in notifications"
      :key="notification.id"
      :notification="notification"
    ></Notification>
  </div>
</template>

<script>
import { mapState } from 'vuex'

import Notification from '@/components/notifications/Notification'

export default {
  name: 'Notifications',
  components: { Notification },
  computed: {
    ...mapState({
      notifications: state => state.notification.items
    })
  }
}
</script>
