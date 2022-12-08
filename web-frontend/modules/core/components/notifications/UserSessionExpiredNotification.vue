<template>
  <Alert
    simple
    shadow
    type="info"
    icon="exclamation"
    :title="$t('UserSessionExpiredNotification.title')"
  >
    {{ $t('UserSessionExpiredNotification.content') }}
  </Alert>
</template>

<script>
export default {
  name: 'UserSessionExpiredNotification',
  mounted() {
    setTimeout(() => {
      this.acknowledge()
    }, 7000)
  },
  beforeDestroy() {
    this.acknowledge()
  },
  methods: {
    acknowledge() {
      this.$store.dispatch('notification/setUserSessionExpired', false)
    },
  },
}
</script>
