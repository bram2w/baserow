<template>
  <nuxt-link
    class="notification-panel__notification-link"
    :to="{ name: 'dashboard' }"
    @click.native="markAsReadAndHandleClick"
  >
    <div class="notification-panel__notification-content-title">
      <i18n path="workspaceInvitationCreatedNotification.title" tag="span">
        <template #sender>
          <strong>{{ notification.sender.first_name }}</strong>
        </template>
        <template #workspaceName>
          <strong>{{ notification.data.invited_to_workspace_name }}</strong>
        </template>
      </i18n>
    </div>
  </nuxt-link>
</template>

<script>
import notificationContent from '@baserow/modules/core/mixins/notificationContent'

export default {
  name: 'WorkspaceInvitationCreatedNotification',
  mixins: [notificationContent],
  props: {
    notification: {
      type: Object,
      required: true,
    },
  },
  methods: {
    handleClick() {
      this.$emit('close-panel')
    },
  },
}
</script>
