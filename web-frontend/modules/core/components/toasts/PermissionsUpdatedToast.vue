<template>
  <Toast
    close-button
    type="warning"
    icon="iconoir-warning-triangle"
    :loading="loading"
    @close="close"
  >
    <template #title>{{ $t('permissionsUpdatedToast.title') }}</template>
    <span>{{ $t('permissionsUpdatedToast.content') }}</span>
    <template #actions>
      <button
        class="toast__actions-button toast__actions-button--primary"
        :loading="loading"
        @click="reload()"
      >
        {{ $t('permissionsUpdatedToast.action') }}
      </button>
    </template>
  </Toast>
</template>

<script>
import Toast from './Toast.vue'
export default {
  name: 'PermissionsUpdatedToast',
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
    close() {
      this.$store.dispatch('toast/setPermissionsUpdated', false)
    },
  },
}
</script>
