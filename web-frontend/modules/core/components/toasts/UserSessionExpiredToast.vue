<template>
  <Alert
    simple
    shadow
    type="info"
    icon="iconoir-warning-triangle"
    :title="$t('userSessionExpiredToast.title')"
  >
    {{ $t('userSessionExpiredToast.content') }}
  </Alert>
</template>

<script>
export default {
  name: 'UserSessionExpiredToast',
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
      this.$store.dispatch('toast/setUserSessionExpired', false)
    },
  },
}
</script>
