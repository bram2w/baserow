<template>
  <div class="notifications">
    <div class="top-right-notifications">
      <ConnectingNotification v-if="connecting"></ConnectingNotification>
      <FailedConnectingNotification
        v-if="failedConnecting"
      ></FailedConnectingNotification>
      <Notification
        v-for="notification in normalNotifications"
        :key="notification.id"
        :notification="notification"
      ></Notification>
    </div>
    <div class="bottom-right-notifications">
      <CopyingNotification v-if="copying"></CopyingNotification>
      <RestoreNotification
        v-for="notification in restoreNotifications"
        :key="notification.id"
        :notification="notification"
      ></RestoreNotification>
    </div>
  </div>
</template>

<script>
import { mapState } from 'vuex'

import Notification from '@baserow/modules/core/components/notifications/Notification'
import ConnectingNotification from '@baserow/modules/core/components/notifications/ConnectingNotification'
import FailedConnectingNotification from '@baserow/modules/core/components/notifications/FailedConnectingNotification'
import RestoreNotification from '@baserow/modules/core/components/notifications/RestoreNotification'
import CopyingNotification from '@baserow/modules/core/components/notifications/CopyingNotification'

export default {
  name: 'Notifications',
  components: {
    RestoreNotification,
    Notification,
    ConnectingNotification,
    FailedConnectingNotification,
    CopyingNotification,
  },
  computed: {
    restoreNotifications() {
      return this.notifications.filter((n) => n.type === 'restore')
    },
    normalNotifications() {
      return this.notifications.filter((n) => n.type !== 'restore')
    },
    ...mapState({
      connecting: (state) => state.notification.connecting,
      failedConnecting: (state) => state.notification.failedConnecting,
      copying: (state) => state.notification.copying,
      notifications: (state) => state.notification.items,
    }),
  },
}
</script>
