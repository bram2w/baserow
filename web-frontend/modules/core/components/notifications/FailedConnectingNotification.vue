<template>
  <div
    class="alert alert--simple alert--with-shadow alert--has-icon alert--error"
  >
    <div class="alert__icon">
      <i class="fas fa-exclamation"></i>
    </div>
    <div class="alert__title">Failed</div>
    <p class="alert__content">
      Connection to the server has failed. Please refresh the page.
    </p>
    <a
      class="button margin-top-1"
      :class="{ 'button--loading': loading }"
      @click="reload()"
      >Refresh page</a
    >
  </div>
</template>

<script>
export default {
  name: 'FailedConnectingNotification',
  data() {
    return {
      loading: false,
    }
  },
  methods: {
    reload() {
      this.loading = true
      location.reload()
    },
  },
}
</script>
