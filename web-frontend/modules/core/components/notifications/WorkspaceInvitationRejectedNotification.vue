<template>
  <a
    href="#"
    class="notification-panel__notification-link"
    @click="markAsReadAndHandleClick"
  >
    <div class="notification-panel__notification-content-title">
      <i18n path="workspaceInvitationRejectedNotification.title" tag="span">
        <template #sender>
          <strong>{{ notification.sender.first_name }}</strong>
        </template>
        <template #workspaceName>
          <strong>{{ notification.data.invited_to_workspace_name }}</strong>
        </template>
      </i18n>
    </div>
  </a>
</template>

<script>
import notificationContent from '@baserow/modules/core/mixins/notificationContent'

export default {
  name: 'WorkspaceInvitationRejectedNotification',
  mixins: [notificationContent],
  props: {
    notification: {
      type: Object,
      required: true,
    },
  },
}
</script>
