<template>
  <Alert
    simple
    shadow
    close-button
    icon="exclamation"
    :type="notification.type"
    :title="notification.title"
    @close="close(notification)"
  >
    {{ notification.message }}
  </Alert>
</template>

<script>
export default {
  name: 'Notification',
  props: {
    notification: {
      type: Object,
      required: true,
    },
  },
  mounted() {
    setTimeout(() => {
      this.close(this.notification)
    }, 5000)
  },
  methods: {
    close(notification) {
      this.$store.dispatch('notification/remove', notification)
    },
  },
}
</script>
