<template>
  <Toast type="info-neutral" loading>
    <template #title>{{ $t('connectingToast.title') }}</template>
    <span>{{ $t('connectingToast.content') }}</span>
  </Toast>
</template>

<script>
import Toast from '@baserow/modules/core/components/toasts/Toast'
export default {
  name: 'ConnectingToast',
  components: {
    Toast,
  },
}
</script>
