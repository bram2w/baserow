<template>
  <Alert
    shadow
    simple
    type="error"
    icon="iconoir-warning-triangle"
    :title="$t('failedConnectingToast.title')"
  >
    <p>{{ $t('failedConnectingToast.content') }}</p>
    <a
      class="button margin-top-1"
      :class="{ 'button--loading': loading }"
      @click="reload()"
      >{{ $t('failedConnectingToast.action') }}
    </a>
  </Alert>
</template>

<script>
export default {
  name: 'FailedConnectingToast',
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
