<template>
  <div>
    <h2 class="box__title">{{ $t('passwordSettings.title') }}</h2>
    <Error :error="error"></Error>
    <Alert v-if="success" type="success">
      <template #title>{{ $t('passwordSettings.changedTitle') }}</template>
      <p>{{ $t('passwordSettings.changedDescription') }}</p>
    </Alert>
    <form v-if="!success" @submit.prevent="changePassword">
      <FormGroup
        :label="$t('passwordSettings.oldPasswordLabel')"
        small-label
        required
        :error="$v.account.oldPassword.$error"
        class="margin-bottom-2"
      >
        <FormInput
          v-model="account.oldPassword"
          :error="$v.account.oldPassword.$error"
          type="password"
          size="large"
          @blur="$v.account.oldPassword.$touch()"
        ></FormInput>
        <template #error>
          {{ $t('passwordSettings.oldPasswordRequiredError') }}</template
        >
      </FormGroup>

      <PasswordInput
        v-model="account.newPassword"
        :validation-state="$v.account.newPassword"
        :label="$t('passwordSettings.newPasswordLabel')"
        class="margin-bottom-2"
      ></PasswordInput>

      <FormGroup
        :error="$v.account.passwordConfirm.$error"
        :label="$t('passwordSettings.repeatNewPasswordLabel')"
        required
        small-label
        class="margin-bottom-2"
      >
        <FormInput
          v-model="account.passwordConfirm"
          :error="$v.account.passwordConfirm.$error"
          type="password"
          size="large"
          @blur="$v.account.passwordConfirm.$touch()"
        >
        </FormInput>

        <template #error>
          {{ $t('passwordSettings.repeatNewPasswordMatchError') }}</template
        >
      </FormGroup>

      <div class="actions actions--right">
        <Button
          type="primary"
          size="large"
          :loading="loading"
          :disabled="loading"
          icon="iconoir-edit-pencil"
        >
          {{ $t('passwordSettings.submitButton') }}
        </Button>
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
        // Changing the password invalidates all the refresh and access token, so we
        // have to log in again. This can be done with the new password we still have
        // in memory.
        await this.$store.dispatch('auth/login', {
          email: this.$store.getters['auth/getUsername'],
          password: this.account.newPassword,
        })
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
