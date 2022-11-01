<template>
  <div>
    <div v-if="!success">
      <div class="auth__logo">
        <nuxt-link :to="{ name: 'index' }">
          <img src="@baserow/modules/core/static/img/logo.svg" alt="" />
        </nuxt-link>
      </div>
      <div class="auth__head auth__head--more-margin">
        <h1 class="auth__head-title">{{ $t('resetPassword.title') }}</h1>
        <LangPicker />
      </div>
      <!-- Disabled info message -->
      <template v-if="!settings.allow_reset_password">
        <Alert
          simple
          type="error"
          icon="exclamation"
          :title="$t('resetPassword.disabled')"
          >{{ $t('resetPassword.disabledMessage') }}</Alert
        >
        <nuxt-link :to="{ name: 'login' }" class="button button--full-width">
          <i class="fas fa-arrow-left"></i>
          {{ $t('action.backToLogin') }}
        </nuxt-link>
      </template>

      <!-- Form -->
      <div v-else>
        <Error :error="error"></Error>
        <form @submit.prevent="resetPassword">
          <div class="auth__control">
            <label class="auth__control-label">{{
              $t('resetPassword.newPassword')
            }}</label>
            <div class="control__elements">
              <PasswordInput
                v-model="account.password"
                :validation-state="$v.account.password"
                :placeholder="$t('signup.passwordPlaceholder')"
                :error-placeholder-class="'auth__control-error'"
                :show-error-icon="true"
              />
            </div>
          </div>
          <div class="auth__control">
            <label class="auth__control-label">{{
              $t('resetPassword.repeatNewPassword')
            }}</label>
            <div class="control__elements">
              <input
                v-model="account.passwordConfirm"
                :class="{ 'input--error': $v.account.passwordConfirm.$error }"
                type="password"
                class="input input--large"
                @blur="$v.account.passwordConfirm.$touch()"
              />
              <div class="auth__control-error">
                <div v-if="$v.account.passwordConfirm.$error" class="error">
                  {{ $t('error.notMatchingPassword') }}
                </div>
              </div>
            </div>
          </div>
          <div class="auth__action">
            <button
              :class="{ 'button--loading': loading }"
              class="button button--full-width"
              :disabled="loading"
            >
              {{ $t('resetPassword.submit') }}
            </button>
          </div>
          <div>
            <ul class="auth__action-links">
              <li>
                <nuxt-link :to="{ name: 'login' }">
                  <i class="fas fa-arrow-left"></i>
                  {{ $t('action.backToLogin') }}
                </nuxt-link>
              </li>
            </ul>
          </div>
        </form>
      </div>
    </div>
    <div v-if="success" class="box__message">
      <div class="box__message-icon">
        <i class="fas fa-check"></i>
      </div>
      <h1 class="box__message-title">{{ $t('resetPassword.changed') }}</h1>
      <nuxt-link :to="{ name: 'login' }" class="button button--large">
        <i class="fas fa-arrow-left"></i>
        {{ $t('action.backToLogin') }}
      </nuxt-link>
    </div>
  </div>
</template>

<script>
import { sameAs } from 'vuelidate/lib/validators'

import PasswordInput from '@baserow/modules/core/components/helpers/PasswordInput'
import LangPicker from '@baserow/modules/core/components/LangPicker'
import { passwordValidation } from '@baserow/modules/core/validators'
import { ResponseErrorMessage } from '@baserow/modules/core/plugins/clientHandler'
import error from '@baserow/modules/core/mixins/error'
import AuthService from '@baserow/modules/core/services/auth'
import { mapGetters } from 'vuex'

export default {
  components: { LangPicker, PasswordInput },
  mixins: [error],
  layout: 'login',
  data() {
    return {
      loading: false,
      success: false,
      account: {
        password: '',
        passwordConfirm: '',
      },
    }
  },
  head() {
    return {
      title: this.$t('resetPassword.title'),
    }
  },
  computed: {
    ...mapGetters({
      settings: 'settings/get',
    }),
  },
  methods: {
    async resetPassword() {
      this.$v.$touch()
      if (this.$v.$invalid) {
        return
      }

      this.loading = true
      this.hideError()

      try {
        const token = this.$route.params.token
        await AuthService(this.$client).resetPassword(
          token,
          this.account.password
        )
        this.success = true
        this.loading = false
      } catch (error) {
        this.loading = false
        this.handleError(error, 'resetPassword', {
          BAD_TOKEN_SIGNATURE: new ResponseErrorMessage(
            this.$t('resetPassword.errorInvalidLinkTitle'),
            this.$t('resetPassword.errorInvalidLinkMessage')
          ),
          EXPIRED_TOKEN_SIGNATURE: new ResponseErrorMessage(
            this.$t('resetPassword.errorLinkExpiredTitle'),
            this.$t('resetPassword.errorLinkExpiredMessage')
          ),
        })
      }
    },
  },
  validations: {
    account: {
      password: passwordValidation,
      passwordConfirm: {
        sameAsPassword: sameAs('password'),
      },
    },
  },
}
</script>
