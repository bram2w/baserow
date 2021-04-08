<template>
  <div class="notifications">
    <ConnectingNotification v-if="connecting"></ConnectingNotification>
    <FailedConnectingNotification
      v-if="failedConnecting"
    ></FailedConnectingNotification>
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
import FailedConnectingNotification from '@baserow/modules/core/components/notifications/FailedConnectingNotification'

export default {
  name: 'Notifications',
  components: {
    Notification,
    ConnectingNotification,
    FailedConnectingNotification,
  },
  computed: {
    ...mapState({
      connecting: (state) => state.notification.connecting,
      failedConnecting: (state) => state.notification.failedConnecting,
      notifications: (state) => state.notification.items,
    }),
  },
}
</script>
