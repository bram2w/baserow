<template>
  <Alert
    v-if="application.untrusted_content"
    v-tooltip="message"
    type="warning"
    role="alert"
    :aria-label="message"
    class="header__alert"
  >
    {{ $t('applicationUntrustedContentAlert.title') }}
  </Alert>
</template>

<script setup>
import Alert from '@baserow/modules/core/components/Alert'

defineProps({
  application: {
    type: Object,
    required: true,
  },
  message: {
    type: String,
    required: true,
  },
})
</script>
