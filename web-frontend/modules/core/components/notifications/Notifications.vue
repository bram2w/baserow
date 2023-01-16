<template>
  <div class="notifications">
    <div class="top-right-notifications">
      <PermissionsUpdatedNotification v-if="permissionsUpdated" />
      <ConnectingNotification v-if="connecting"></ConnectingNotification>
      <UserSessionExpiredNotification
        v-if="isUserSessionExpired"
      ></UserSessionExpiredNotification>
      <FailedConnectingNotification
        v-if="failedConnecting"
      ></FailedConnectingNotification>
      <AuthorizationErrorNotification
        v-if="unauthorized"
      ></AuthorizationErrorNotification>
      <Notification
        v-for="notification in normalNotifications"
        :key="notification.id"
        :notification="notification"
      ></Notification>
    </div>
    <div class="bottom-right-notifications">
      <UndoRedoNotification
        v-if="undoRedoIsNotHidden"
        :state="undoRedoState"
      ></UndoRedoNotification>
      <CopyingNotification v-if="copying"></CopyingNotification>
      <PastingNotification v-if="pasting"></PastingNotification>
      <ClearingNotification v-if="clearing"></ClearingNotification>
      <RestoreNotification
        v-for="notification in restoreNotifications"
        :key="notification.id"
        :notification="notification"
      ></RestoreNotification>
    </div>
  </div>
</template>

<script>
import { mapGetters, mapState } from 'vuex'

import Notification from '@baserow/modules/core/components/notifications/Notification'
import ConnectingNotification from '@baserow/modules/core/components/notifications/ConnectingNotification'
import FailedConnectingNotification from '@baserow/modules/core/components/notifications/FailedConnectingNotification'
import RestoreNotification from '@baserow/modules/core/components/notifications/RestoreNotification'
import CopyingNotification from '@baserow/modules/core/components/notifications/CopyingNotification'
import PastingNotification from '@baserow/modules/core/components/notifications/PastingNotification'
import ClearingNotification from '@baserow/modules/core/components/notifications/ClearingNotification'
import AuthorizationErrorNotification from '@baserow/modules/core/components/notifications/AuthorizationErrorNotification'
import UserSessionExpiredNotification from '@baserow/modules/core/components/notifications/UserSessionExpiredNotification'
import UndoRedoNotification from '@baserow/modules/core/components/notifications/UndoRedoNotification'
import { UNDO_REDO_STATES } from '@baserow/modules/core/utils/undoRedoConstants'
import PermissionsUpdatedNotification from '@baserow/modules/core/components/notifications/PermissionsUpdatedNotification'

export default {
  name: 'Notifications',
  components: {
    PermissionsUpdatedNotification,
    RestoreNotification,
    Notification,
    ConnectingNotification,
    FailedConnectingNotification,
    CopyingNotification,
    PastingNotification,
    ClearingNotification,
    AuthorizationErrorNotification,
    UndoRedoNotification,
    UserSessionExpiredNotification,
  },
  computed: {
    undoRedoIsNotHidden() {
      return this.undoRedoState !== UNDO_REDO_STATES.HIDDEN
    },
    restoreNotifications() {
      return this.notifications.filter((n) => n.type === 'restore')
    },
    normalNotifications() {
      return this.notifications.filter((n) => n.type !== 'restore')
    },
    ...mapState({
      unauthorized: (state) => state.notification.authorizationError,
      connecting: (state) => state.notification.connecting,
      failedConnecting: (state) => state.notification.failedConnecting,
      copying: (state) => state.notification.copying,
      pasting: (state) => state.notification.pasting,
      clearing: (state) => state.notification.clearing,
      notifications: (state) => state.notification.items,
      undoRedoState: (state) => state.notification.undoRedoState,
      isUserSessionExpired: (state) => state.notification.userSessionExpired,
      permissionsUpdated: (state) => state.notification.permissionsUpdated,
    }),
    ...mapGetters({ isAuthenticated: 'auth/isAuthenticated' }),
  },
  watch: {
    isAuthenticated(value) {
      if (!value) {
        this.$store.dispatch('notification/userLoggedOut')
      }
    },
  },
}
</script>
