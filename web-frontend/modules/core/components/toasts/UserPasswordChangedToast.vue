<template>
  <Alert
    simple
    shadow
    type="info"
    icon="iconoir-warning-triangle"
    :title="$t('userPasswordChangedToast.title')"
  >
    <p>{{ $t('userPasswordChangedToast.content') }}</p>
  </Alert>
</template>

<script>
export default {
  name: 'UserPasswordChangedToast',
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
      this.$store.dispatch('toast/setUserPasswordChanged', false)
    },
  },
}
</script>
