<template>
  <form @submit.prevent="submit">
    <div class="control">
      <label class="control__label">New password</label>
      <div class="control__elements">
        <PasswordInput
          v-model="values.password"
          :validation-state="$v.values.password"
        />
      </div>
    </div>
    <div class="control">
      <label class="control__label">Repeat password</label>
      <div class="control__elements">
        <input
          v-model="values.passwordConfirm"
          :class="{ 'input--error': $v.values.passwordConfirm.$error }"
          type="password"
          class="input input--large"
          @blur="$v.values.passwordConfirm.$touch()"
        />
        <div v-if="$v.values.passwordConfirm.$error" class="error">
          This field must match your password field.
        </div>
      </div>
    </div>
    <div class="actions">
      <div class="align-right">
        <button
          class="button button--large button--primary"
          :class="{ 'button--loading': loading }"
          :disabled="loading"
        >
          Change password
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
