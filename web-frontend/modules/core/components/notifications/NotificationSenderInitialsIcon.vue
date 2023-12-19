<template functional>
  <div class="notification-panel__notification-user-initials">
    {{ props.notification.sender?.first_name | nameAbbreviation }}
  </div>
</template>

<script>
export default {
  name: 'NotificationSenderInitialsIcon',
  functional: true,
}
</script>
