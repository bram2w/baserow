<template>
  <Alert v-if="shouldBeDisplayed" type="info-primary">
    <template #title> {{ $t('dashboardVerifyEmail.title') }}</template>
    <template #actions>
      <Button
        type="primary"
        size="small"
        :disabled="resendLoading || resendSuccess"
        :loading="resendLoading"
        @click="resend(user.username)"
      >
        {{ $t('dashboardVerifyEmail.resendConfirmationEmail') }}
      </Button>
    </template>
  </Alert>
</template>

<script>
import { mapState } from 'vuex'
import { EMAIL_VERIFICATION_OPTIONS } from '@baserow/modules/core/enums'
import resendEmailVerification from '@baserow/modules/core/mixins/resendEmailVerification'

export default {
  name: 'DashboardVerifyEmail',
  mixins: [resendEmailVerification],
  computed: {
    ...mapState({
      user: (state) => state.auth.user,
      settings: (state) => state.settings.settings,
      refreshTokenPayload: (state) => state.auth.refreshTokenPayload,
    }),
    shouldBeDisplayed() {
      if (
        [
          EMAIL_VERIFICATION_OPTIONS.RECOMMENDED,
          EMAIL_VERIFICATION_OPTIONS.ENFORCED,
        ].includes(this.settings.email_verification) &&
        this.user.email_verified === false &&
        this.refreshTokenPayload?.verified_email_claim ===
          EMAIL_VERIFICATION_OPTIONS.ENFORCED
      ) {
        return true
      }
      return false
    },
  },
}
</script>
