<template>
  <div>
    <div v-if="!success">
      <div class="box__head">
        <h1 class="box__head-title">{{ $t('resetPassword.title') }}</h1>
        <LangPicker />
      </div>
      <Error :error="error"></Error>
      <form @submit.prevent="resetPassword">
        <div class="control">
          <label class="control__label">{{
            $t('resetPassword.newPassword')
          }}</label>
          <div class="control__elements">
            <PasswordInput
              v-model="account.password"
              :validation-state="$v.account.password"
            />
          </div>
        </div>
        <div class="control">
          <label class="control__label">{{
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
            <div v-if="$v.account.passwordConfirm.$error" class="error">
              {{ $t('error.notMatchingPassword') }}
            </div>
          </div>
        </div>
        <div class="actions">
          <ul class="action__links">
            <li>
              <nuxt-link :to="{ name: 'login' }">
                <i class="fas fa-arrow-left"></i>
                {{ $t('action.backToLogin') }}
              </nuxt-link>
            </li>
          </ul>
          <button
            :class="{ 'button--loading': loading }"
            class="button button--large"
            :disabled="loading"
          >
            {{ $t('resetPassword.submit') }}
            <i class="fas fa-pencil-alt"></i>
          </button>
        </div>
      </form>
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
      title: 'Reset password',
    }
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

<i18n>
{
  "en": {
    "resetPassword": {
      "title": "Reset password",
      "newPassword": "New password",
      "repeatNewPassword": "Repeat new password",
      "submit": "Change password",
      "changed": "Password changed",
      "errorInvalidLinkTitle": "Invalid link",
      "errorInvalidLinkMessage": "Could not reset the password because the link is invalid.",
      "errorLinkExpiredTitle": "Link expired",
      "errorLinkExpiredMessage": "The password reset link has expired. Please request another one."
    }
  },
  "fr": {
    "resetPassword": {
      "title": "Nouveau mot de passe",
      "newPassword": "Nouveau mot de passe",
      "repeatNewPassword": "Répetez le mot de passe",
      "submit": "Mettre à jour",
      "changed": "Mot de passe mis à jour",
      "errorInvalidLinkTitle": "Lien invalid",
      "errorInvalidLinkMessage": "Il n'est pas possible de réinitialiser le mot de passe car le lien est invalide.",
      "errorLinkExpiredTitle": "Lien expiré",
      "errorLinkExpiredMessage": "Le lien de réinitialisation de mot de passe a expiré, Veuillez en demander un nouveau."
    }
  }
}
</i18n>
