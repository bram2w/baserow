<template>
  <div>
    <div class="box__message">
      <div class="box__message-icon">
        <i class="iconoir-mail-out"></i>
      </div>
      <p class="box__message-text">
        {{ $t('verifyEmailAddress.confirmation') }}
      </p>
      <Button
        tag="nuxt-link"
        :to="{ name: 'login' }"
        type="secondary"
        size="large"
      >
        {{ $t('verifyEmailAddress.goToDashboard') }}</Button
      >
    </div>
  </div>
</template>

<script>
import AuthService from '@baserow/modules/core/services/auth'

export default {
  layout: 'login',
  async asyncData({ store, params, error, app, redirect }) {
    const { token } = params
    try {
      await AuthService(app.$client).verifyEmail(token)
      const user = store.getters['auth/getUserObject']
      if (user !== null) {
        store.dispatch('auth/forceUpdateUserData', {
          user: {
            email_verified: true,
          },
        })
      }
    } catch {
      return error({
        statusCode: 404,
        message: 'Not a valid confirmation token.',
      })
    }
  },
}
</script>
