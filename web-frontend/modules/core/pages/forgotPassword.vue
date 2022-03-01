<template>
  <div>
    <div v-if="!success">
      <div class="box__head">
        <h1 class="box__head-title">{{ $t('forgotPassword.title') }}</h1>
        <LangPicker />
      </div>
      <p>
        {{ $t('forgotPassword.message') }}
      </p>
      <Error :error="error"></Error>
      <form @submit.prevent="sendLink">
        <div class="control">
          <label class="control__label">{{ $t('field.emailAddress') }}</label>
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
              {{ $t('error.invalidEmail') }}
            </div>
          </div>
        </div>
        <div class="actions">
          <ul class="action__links">
            <li>
              <nuxt-link :to="{ name: 'login' }">
                <i class="fas fa-arrow-left"></i>
                {{ $t('action.back') }}
              </nuxt-link>
            </li>
          </ul>
          <button
            :class="{ 'button--loading': loading }"
            class="button button--large"
            :disabled="loading || success"
          >
            {{ $t('forgotPassword.submit') }}
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
        {{ $t('forgotPassword.confirmation') }}
      </p>
      <nuxt-link :to="{ name: 'login' }" class="button button--large">
        <i class="fas fa-arrow-left"></i>
        {{ $t('action.backToLogin') }}
      </nuxt-link>
    </div>
  </div>
</template>

<script>
import { required, email } from 'vuelidate/lib/validators'

import error from '@baserow/modules/core/mixins/error'
import AuthService from '@baserow/modules/core/services/auth'
import LangPicker from '@baserow/modules/core/components/LangPicker'

export default {
  components: { LangPicker },
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
      title: this.$t('forgotPassword.title'),
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
