<template>
  <div>
    <div class="toast__top-right">
      <PermissionsUpdatedToast v-if="permissionsUpdated" />
      <ConnectingToast v-if="connecting"></ConnectingToast>
      <UserSessionExpiredToast
        v-if="isUserSessionExpired"
      ></UserSessionExpiredToast>
      <FailedConnectingToast v-if="failedConnecting"></FailedConnectingToast>
      <AuthorizationErrorToast v-if="unauthorized"></AuthorizationErrorToast>
      <Toast
        v-for="toast in normalToasts"
        :key="toast.id"
        :toast="toast"
      ></Toast>
    </div>
    <div class="toast__bottom-right">
      <UndoRedoToast
        v-if="undoRedoIsNotHidden"
        :state="undoRedoState"
      ></UndoRedoToast>
      <CopyingToast v-if="copying"></CopyingToast>
      <PastingToast v-if="pasting"></PastingToast>
      <ClearingToast v-if="clearing"></ClearingToast>
      <RestoreToast
        v-for="toast in restoreToasts"
        :key="toast.id"
        :toast="toast"
      ></RestoreToast>
    </div>
  </div>
</template>

<script>
import { mapGetters, mapState } from 'vuex'

import Toast from '@baserow/modules/core/components/toasts/Toast'
import ConnectingToast from '@baserow/modules/core/components/toasts/ConnectingToast'
import FailedConnectingToast from '@baserow/modules/core/components/toasts/FailedConnectingToast'
import RestoreToast from '@baserow/modules/core/components/toasts/RestoreToast'
import CopyingToast from '@baserow/modules/core/components/toasts/CopyingToast'
import PastingToast from '@baserow/modules/core/components/toasts/PastingToast'
import ClearingToast from '@baserow/modules/core/components/toasts/ClearingToast'
import AuthorizationErrorToast from '@baserow/modules/core/components/toasts/AuthorizationErrorToast'
import UserSessionExpiredToast from '@baserow/modules/core/components/toasts/UserSessionExpiredToast'
import UndoRedoToast from '@baserow/modules/core/components/toasts/UndoRedoToast'
import { UNDO_REDO_STATES } from '@baserow/modules/core/utils/undoRedoConstants'
import PermissionsUpdatedToast from '@baserow/modules/core/components/toasts/PermissionsUpdatedToast'

export default {
  name: 'Toasts',
  components: {
    PermissionsUpdatedToast,
    RestoreToast,
    Toast,
    ConnectingToast,
    FailedConnectingToast,
    CopyingToast,
    PastingToast,
    ClearingToast,
    AuthorizationErrorToast,
    UndoRedoToast,
    UserSessionExpiredToast,
  },
  computed: {
    undoRedoIsNotHidden() {
      return this.undoRedoState !== UNDO_REDO_STATES.HIDDEN
    },
    restoreToasts() {
      return this.toasts.filter((n) => n.type === 'restore')
    },
    normalToasts() {
      return this.toasts.filter((n) => n.type !== 'restore')
    },
    ...mapState({
      unauthorized: (state) => state.toast.authorizationError,
      connecting: (state) => state.toast.connecting,
      failedConnecting: (state) => state.toast.failedConnecting,
      copying: (state) => state.toast.copying,
      pasting: (state) => state.toast.pasting,
      clearing: (state) => state.toast.clearing,
      toasts: (state) => state.toast.items,
      undoRedoState: (state) => state.toast.undoRedoState,
      isUserSessionExpired: (state) => state.toast.userSessionExpired,
      permissionsUpdated: (state) => state.toast.permissionsUpdated,
    }),
    ...mapGetters({ isAuthenticated: 'auth/isAuthenticated' }),
  },
  watch: {
    isAuthenticated(value) {
      if (!value) {
        this.$store.dispatch('toast/userLoggedOut')
      }
    },
  },
}
</script>
