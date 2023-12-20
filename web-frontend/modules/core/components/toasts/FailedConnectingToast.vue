<template>
  <Toast type="error" icon="iconoir-warning-triangle">
    <template #title>{{ $t('failedConnectingToast.title') }}</template>
    <span>{{ $t('failedConnectingToast.content') }}</span>
    <template #actions>
      <button
        class="toast__actions-button toast__actions-button--primary"
        :class="{ 'toast__actions-button--loading': loading }"
        @click="reload()"
      >
        {{ $t('failedConnectingToast.action') }}
      </button>
    </template>
  </Toast>
</template>

<script>
import Toast from '@baserow/modules/core/components/toasts/Toast'
export default {
  name: 'FailedConnectingToast',
  components: {
    Toast,
  },
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
