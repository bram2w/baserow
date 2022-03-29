<template>
  <form @submit.prevent="submit">
    <FormElement :error="fieldHasErrors('password')" class="control">
      <label class="control__label">{{
        $t('changePasswordForm.newPassword')
      }}</label>
      <div class="control__elements">
        <PasswordInput
          v-model="values.password"
          :validation-state="$v.values.password"
        />
      </div>
    </FormElement>
    <FormElement :error="fieldHasErrors('passwordConfirm')" class="control">
      <label class="control__label">{{
        $t('changePasswordForm.repeatPassword')
      }}</label>
      <div class="control__elements">
        <input
          v-model="values.passwordConfirm"
          :class="{ 'input--error': fieldHasErrors('passwordConfirm') }"
          type="password"
          class="input input--large"
          @blur="$v.values.passwordConfirm.$touch()"
        />
        <div v-if="fieldHasErrors('passwordConfirm')" class="error">
          {{ $t('changePasswordForm.error.doesntMatch') }}
        </div>
      </div>
    </FormElement>
    <div class="actions">
      <div class="align-right">
        <button
          class="button button--large button--primary"
          :class="{ 'button--loading': loading }"
          :disabled="loading"
        >
          {{ $t('changePasswordForm.changePassword') }}
        </button>
      </div>
    </div>
  </form>
</template>

<script>
import { sameAs } from 'vuelidate/lib/validators'
import PasswordInput from '@baserow/modules/core/components/helpers/PasswordInput'
import { passwordValidation } from '@baserow/modules/core/validators'

import form from '@baserow/modules/core/mixins/form'

export default {
  name: 'ChangePasswordForm',
  components: { PasswordInput },
  mixins: [form],
  props: {
    loading: {
      type: Boolean,
      required: true,
    },
  },
  data() {
    return {
      allowedValues: ['password', 'passwordConfirm'],
      values: {
        password: '',
        passwordConfirm: '',
      },
    }
  },
  validations: {
    values: {
      passwordConfirm: {
        sameAsPassword: sameAs('password'),
      },
      password: passwordValidation,
    },
  },
}
</script>
