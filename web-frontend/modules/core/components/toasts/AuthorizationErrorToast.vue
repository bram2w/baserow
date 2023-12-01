<template>
  <Toast type="error" icon="iconoir-warning-triangle">
    <template #title>{{ $t('authorizationErrorToast.title') }}</template>
    <span> {{ $t('authorizationErrorToast.content') }}</span>
    <template #actions>
      <button
        class="toast__actions-button toast__actions-button--primary"
        :class="{ 'toast__actions-button--loading': loading }"
        @click="reload()"
      >
        {{ $t('authorizationErrorToast.action') }}
      </button>
    </template>
  </Toast>
</template>

<script>
import Toast from '@baserow/modules/core/components/toasts/Toast'
export default {
  name: 'AuthorizationErrorToast',
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
