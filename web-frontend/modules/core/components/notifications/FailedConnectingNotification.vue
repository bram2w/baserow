<template>
  <Alert
    shadow
    simple
    type="error"
    icon="exclamation"
    :title="$t('failedConnectingNotification.title')"
    >{{ $t('failedConnectingNotification.content') }}
    <a
      class="button margin-top-1"
      :class="{ 'button--loading': loading }"
      @click="reload()"
      >{{ $t('failedConnectingNotification.action') }}
    </a>
  </Alert>
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
