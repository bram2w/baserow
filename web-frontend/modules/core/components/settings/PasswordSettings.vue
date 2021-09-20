<template>
  <div>
    <h2 class="box__title">{{ $t('passwordSettings.title') }}</h2>
    <Error :error="error"></Error>
    <div v-if="success" class="alert alert--success alert--has-icon">
      <div class="alert__icon">
        <i class="fas fa-check"></i>
      </div>
      <div class="alert__title">
        {{ $t('passwordSettings.changedTitle') }}
      </div>
      <p class="alert__content">
        {{ $t('passwordSettings.changedDescription') }}
      </p>
    </div>
    <form v-if="!success" @submit.prevent="changePassword">
      <div class="control">
        <label class="control__label">{{
          $t('passwordSettings.oldPasswordLabel')
        }}</label>
        <div class="control__elements">
          <input
            v-model="account.oldPassword"
            :class="{ 'input--error': $v.account.oldPassword.$error }"
            type="password"
            class="input input--large"
            @blur="$v.account.oldPassword.$touch()"
          />
          <div v-if="$v.account.oldPassword.$error" class="error">
            {{ $t('passwordSettings.oldPasswordRequiredError') }}
          </div>
        </div>
      </div>
      <div class="control">
        <label class="control__label">{{
          $t('passwordSettings.newPasswordLabel')
        }}</label>
        <div class="control__elements">
          <PasswordInput
            v-model="account.newPassword"
            :validation-state="$v.account.newPassword"
          />
        </div>
      </div>
      <div class="control">
        <label class="control__label">{{
          $t('passwordSettings.repeatNewPasswordLabel')
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
            {{ $t('passwordSettings.repeatNewPasswordMatchError') }}
          </div>
        </div>
      </div>
      <div class="actions actions--right">
        <button
          :class="{ 'button--loading': loading }"
          class="button button--large"
          :disabled="loading"
        >
          {{ $t('passwordSettings.submitButton') }}
          <i class="fas fa-pencil-alt"></i>
        </button>
      </div>
    </form>
  </div>
</template>

<script>
import { sameAs, required } from 'vuelidate/lib/validators'

import { ResponseErrorMessage } from '@baserow/modules/core/plugins/clientHandler'
import error from '@baserow/modules/core/mixins/error'
import AuthService from '@baserow/modules/core/services/auth'
import PasswordInput from '@baserow/modules/core/components/helpers/PasswordInput'
import { passwordValidation } from '@baserow/modules/core/validators'

export default {
  components: { PasswordInput },
  mixins: [error],
  layout: 'login',
  data() {
    return {
      loading: false,
      success: false,
      account: {
        oldPassword: '',
        newPassword: '',
        passwordConfirm: '',
      },
    }
  },
  methods: {
    async changePassword() {
      this.$v.$touch()

      if (this.$v.$invalid) {
        return
      }

      this.loading = true
      this.hideError()

      try {
        await AuthService(this.$client).changePassword(
          this.account.oldPassword,
          this.account.newPassword
        )
        this.success = true
        this.loading = false
      } catch (error) {
        this.loading = false
        this.handleError(error, 'changePassword', {
          ERROR_INVALID_OLD_PASSWORD: new ResponseErrorMessage(
            this.$t('passwordSettings.errorInvalidOldPasswordTitle'),
            this.$t('passwordSettings.errorInvalidOldPasswordMessage')
          ),
        })
      }
    },
  },
  validations: {
    account: {
      passwordConfirm: {
        sameAsPassword: sameAs('newPassword'),
      },
      newPassword: passwordValidation,
      oldPassword: { required },
    },
  },
}
</script>

<i18n>
{
  "en": {
    "passwordSettings": {
      "title": "Change password",
      "changedTitle": "Password changed",
      "changedDescription": "Your password has been changed. The next time you want to login, you have to use your new password.",
      "oldPasswordLabel": "Old password",
      "oldPasswordRequiredError": "Old password is required.",
      "newPasswordLabel": "New password",
      "repeatNewPasswordLabel": "Repeat new password",
      "repeatNewPasswordMatchError": "This field must match your new password field.",
      "submitButton": "Change password",
      "errorInvalidOldPasswordTitle": "Invalid password",
      "errorInvalidOldPasswordMessage": "Could not change your password because your old password is invalid."
    }
  },
  "fr": {
    "passwordSettings": {
      "title": "Mise à jour du mot de passe",
      "changedTitle": "Mot de passe mis à jour",
      "changedDescription": "Votre mot de passe a été mis à jour. La prochaine fois que vous souhaitez vous connecter, vous devrez utiliser le nouveau mot de passe",
      "oldPasswordLabel": "Ancien mot de passe",
      "oldPasswordRequiredError": "L'ancien mot de passe est obligatoire",
      "newPasswordLabel": "Nouveau mot de passe",
      "repeatNewPasswordLabel": "Répétez le mot de passe",
      "repeatNewPasswordMatchError": "Les deux mots de passe ne correspondent pas.",
      "submitButton": "Mettre à jour",
      "errorInvalidOldPasswordTitle": "Ancien mot de passe invalide",
      "errorInvalidOldPasswordMessage": "Impossible de mettre à jour votre mot de passe car votre ancien mot de passe est invalide."
    }
  }
}
</i18n>
