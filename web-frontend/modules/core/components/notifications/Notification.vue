<template>
  <div
    class="alert alert--simple alert--with-shadow alert--has-icon"
    :class="notificationClass"
  >
    <a class="alert__close" @click="close(notification)">
      <i class="fas fa-times"></i>
    </a>
    <div class="alert__icon">
      <i class="fas fa-exclamation"></i>
    </div>
    <div class="alert__title">{{ notification.title }}</div>
    <p class="alert__content">{{ notification.message }}</p>
  </div>
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
  computed: {
    notificationClass() {
      return 'alert--' + this.notification.type
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
