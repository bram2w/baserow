<template>
  <div>
    <h2 class="box__title">Change password</h2>
    <Error :error="error"></Error>
    <div v-if="success" class="alert alert--success alert--has-icon">
      <div class="alert__icon">
        <i class="fas fa-check"></i>
      </div>
      <div class="alert__title">Password changed</div>
      <p class="alert__content">
        Your password has been changed. The next time you want to login, you
        have to use your new password.
      </p>
    </div>
    <form v-if="!success" @submit.prevent="changePassword">
      <div class="control">
        <label class="control__label">Old password</label>
        <div class="control__elements">
          <input
            v-model="account.oldPassword"
            :class="{ 'input--error': $v.account.oldPassword.$error }"
            type="password"
            class="input input--large"
            @blur="$v.account.oldPassword.$touch()"
          />
          <div v-if="$v.account.oldPassword.$error" class="error">
            Old password is required.
          </div>
        </div>
      </div>
      <div class="control">
        <label class="control__label">New password</label>
        <div class="control__elements">
          <PasswordInput
            v-model="account.newPassword"
            :validation-state="$v.account.newPassword"
          />
        </div>
      </div>
      <div class="control">
        <label class="control__label">Repeat new password</label>
        <div class="control__elements">
          <input
            v-model="account.passwordConfirm"
            :class="{ 'input--error': $v.account.passwordConfirm.$error }"
            type="password"
            class="input input--large"
            @blur="$v.account.passwordConfirm.$touch()"
          />
          <div v-if="$v.account.passwordConfirm.$error" class="error">
            This field must match your new password field.
          </div>
        </div>
      </div>
      <div class="actions actions--right">
        <button
          :class="{ 'button--loading': loading }"
          class="button button--large"
          :disabled="loading"
        >
          Change password
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
            'Invalid password.',
            'Could not change your password because your old password is invalid.'
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
