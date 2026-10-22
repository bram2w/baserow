<template>
  <Alert
    v-if="contentOwner?.untrusted_content"
    v-tooltip="message"
    type="warning"
    role="alert"
    :aria-label="message"
    class="header__alert"
  >
    <span class="header__alert-label">{{
      $t('applicationUntrustedContentAlert.title')
    }}</span>
    <a href="#" @click.prevent="reviewModal.show()">{{
      $t('applicationUntrustedContentAlert.review')
    }}</a>
  </Alert>
  <UntrustedContentReviewModal
    ref="reviewModal"
    :report="contentOwner?.import_report || []"
    :can-trust="canTrust"
    :trust-content="trustContent"
  />
</template>

<script setup>
import { ref } from 'vue'
import Alert from '@baserow/modules/core/components/Alert'
import UntrustedContentReviewModal from '@baserow/modules/core/components/application/UntrustedContentReviewModal'

defineProps({
  contentOwner: { type: Object, default: null },
  canTrust: { type: Boolean, default: false },
  trustContent: { type: Function, required: true },
  message: { type: String, required: true },
})
const reviewModal = ref(null)
</script>
