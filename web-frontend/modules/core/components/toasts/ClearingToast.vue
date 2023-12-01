<template>
  <Toast type="info-primary" loading>
    <template #title>{{ $t('clearingToast.title') }}</template>
    <span>{{ $t('clearingToast.content') }}</span>
  </Toast>
</template>

<script>
import Toast from '@baserow/modules/core/components/toasts/Toast'
export default {
  name: 'ClearingToast',
  components: {
    Toast,
  },
}
</script>
