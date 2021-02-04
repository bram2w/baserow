<template>
  <div>
    <div v-if="!success">
      <h1 class="box__title">Forgot password</h1>
      <p>
        Please enter your e-mail address in the form. If we find an account then
        we will send an e-mail with a link to reset your password.
      </p>
      <Error :error="error"></Error>
      <form @submit.prevent="sendLink">
        <div class="control">
          <label class="control__label">E-mail address</label>
          <div class="control__elements">
            <input
              ref="email"
              v-model="account.email"
              :class="{ 'input--error': $v.account.email.$error }"
              type="text"
              class="input input--large"
              :disabled="success"
              @blur="$v.account.email.$touch()"
            />
            <div v-if="$v.account.email.$error" class="error">
              Please enter a valid e-mail address.
            </div>
          </div>
        </div>
        <div class="actions">
          <ul class="action__links">
            <li>
              <nuxt-link :to="{ name: 'login' }">
                <i class="fas fa-arrow-left"></i>
                Back
              </nuxt-link>
            </li>
          </ul>
          <button
            :class="{ 'button--loading': loading }"
            class="button button--large"
            :disabled="loading || success"
          >
            Send link
            <i class="fas fa-envelope"></i>
          </button>
        </div>
      </form>
    </div>
    <div v-if="success" class="box__message">
      <div class="box__message-icon">
        <i class="fas fa-paper-plane"></i>
      </div>
      <p class="box__message-text">
        If your email address exists in our database, you will receive a
        password reset link at your email address in a few minutes.
      </p>
      <nuxt-link :to="{ name: 'login' }" class="button button--large">
        <i class="fas fa-arrow-left"></i>
        Back to login
      </nuxt-link>
    </div>
  </div>
</template>

<script>
import { required, email } from 'vuelidate/lib/validators'

import error from '@baserow/modules/core/mixins/error'
import AuthService from '@baserow/modules/core/services/auth'

export default {
  mixins: [error],
  layout: 'login',
  data() {
    return {
      loading: false,
      success: false,
      account: {
        email: '',
      },
    }
  },
  head() {
    return {
      title: 'Forgot password',
    }
  },
  methods: {
    async sendLink() {
      this.$v.$touch()
      if (this.$v.$invalid) {
        return
      }

      this.loading = true
      this.hideError()

      try {
        const resetUrl = `${this.$env.PUBLIC_WEB_FRONTEND_URL}/reset-password`
        await AuthService(this.$client).sendResetPasswordEmail(
          this.account.email,
          resetUrl
        )
        this.success = true
        this.loading = false
      } catch (error) {
        this.loading = false
        this.handleError(error, 'passwordReset')
      }
    },
  },
  validations: {
    account: {
      email: { required, email },
    },
  },
}
</script>
