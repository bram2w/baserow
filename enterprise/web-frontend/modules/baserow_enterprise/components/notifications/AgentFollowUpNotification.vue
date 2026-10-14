<template>
  <nuxt-link
    class="notification-panel__notification-link"
    :to="route"
    @click="markAsReadAndHandleClick"
  >
    <div class="notification-panel__notification-content-title">
      <i18n-t
        scope="global"
        keypath="agentFollowUpNotification.title"
        tag="span"
      >
        <template #agent>
          <strong>{{ notification.data.agent_name }}</strong>
        </template>
        <template #title>
          <strong>{{ notification.data.title }}</strong>
        </template>
      </i18n-t>
    </div>
    <div
      v-if="notification.data.message"
      class="notification-panel__notification-content-description"
    >
      {{ notification.data.message }}
    </div>
  </nuxt-link>
</template>

<script>
import notificationContent from '@baserow/modules/core/mixins/notificationContent'

export default {
  name: 'AgentFollowUpNotification',
  mixins: [notificationContent],
  emits: ['close-panel'],
  methods: {
    handleClick() {
      this.$emit('close-panel')
    },
  },
}
</script>
