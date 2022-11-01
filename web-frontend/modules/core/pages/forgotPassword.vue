<template>
  <div>
    <div v-if="!success">
      <div class="auth__logo">
        <nuxt-link :to="{ name: 'index' }">
          <img src="@baserow/modules/core/static/img/logo.svg" alt="" />
        </nuxt-link>
      </div>
      <div class="auth__head auth__head--more-margin">
        <h1 class="auth__head-title">{{ $t('forgotPassword.title') }}</h1>
        <LangPicker />
      </div>

      <!-- Disabled info message -->
      <template v-if="!settings.allow_reset_password">
        <Alert
          simple
          type="error"
          icon="exclamation"
          :title="$t('forgotPassword.disabled')"
          >{{ $t('forgotPassword.disabledMessage') }}</Alert
        >
        <nuxt-link :to="{ name: 'login' }" class="button button--full-width">
          <i class="fas fa-arrow-left"></i>
          {{ $t('action.backToLogin') }}
        </nuxt-link>
      </template>

      <!-- Form -->
      <div v-else>
        <p>
          {{ $t('forgotPassword.message') }}
        </p>
        <Error :error="error"></Error>
        <form @submit.prevent="sendLink">
          <div class="auth__control">
            <label class="auth__control-label">{{
              $t('field.emailAddress')
            }}</label>
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
              <div class="auth__control-error">
                <div v-if="$v.account.email.$error" class="error">
                  <i class="fas fa-fw fa-exclamation-triangle"></i>
                  {{ $t('error.invalidEmail') }}
                </div>
              </div>
            </div>
          </div>
          <div class="auth__action">
            <button
              :class="{ 'button--loading': loading }"
              class="button button--full-width"
              :disabled="loading || success"
            >
              {{ $t('forgotPassword.submit') }}
            </button>
          </div>
          <div>
            <ul class="auth__action-links">
              <li>
                {{ $t('forgotPassword.loginText') }}
                <nuxt-link :to="{ name: 'login' }">
                  {{ $t('action.login') }}
                </nuxt-link>
              </li>
            </ul>
          </div>
        </form>
      </div>
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
import { mapGetters } from 'vuex'

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
  computed: {
    ...mapGetters({
      settings: 'settings/get',
    }),
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
