<template>
  <div>
    <div class="box__message">
      <div class="box__message-icon">
        <i class="iconoir-mail-out"></i>
      </div>
      <p class="box__message-text">
        {{ $t('emailNotVerified.description') }}
      </p>
      <Button
        type="secondary"
        size="large"
        :disabled="resendLoading || resendSuccess"
        :loading="resendLoading"
        @click="resend(email)"
      >
        {{ $t('emailNotVerified.resend') }}
      </Button>
    </div>
  </div>
</template>

<script>
import resendEmailVerification from '@baserow/modules/core/mixins/resendEmailVerification'

export default {
  mixins: [resendEmailVerification],
  props: {
    email: {
      type: String,
      required: true,
    },
  },
}
</script>
