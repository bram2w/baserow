<template>
  <div class="notifications">
    <ConnectingNotification v-if="connecting"></ConnectingNotification>
    <Notification
      v-for="notification in notifications"
      :key="notification.id"
      :notification="notification"
    ></Notification>
  </div>
</template>

<script>
import { mapState } from 'vuex'

import Notification from '@baserow/modules/core/components/notifications/Notification'
import ConnectingNotification from '@baserow/modules/core/components/notifications/ConnectingNotification'

export default {
  name: 'Notifications',
  components: { Notification, ConnectingNotification },
  computed: {
    ...mapState({
      connecting: (state) => state.notification.connecting,
      notifications: (state) => state.notification.items,
    }),
  },
}
</script>
