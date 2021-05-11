<template>
  <form @submit.prevent="submit">
    <div class="control">
      <label class="control__label">New Password</label>
      <div class="control__elements">
        <input
          v-model="values.password"
          :class="{ 'input--error': $v.values.password.$error }"
          type="password"
          class="input input--large"
          @blur="$v.values.password.$touch()"
        />
        <div
          v-if="$v.values.password.$error && !$v.values.password.required"
          class="error"
        >
          A password is required.
        </div>
        <div
          v-if="$v.values.password.$error && !$v.values.password.maxLength"
          class="error"
        >
          A maximum of
          {{ $v.values.password.$params.maxLength.max }} characters is allowed
          here.
        </div>
        <div
          v-if="$v.values.password.$error && !$v.values.password.minLength"
          class="error"
        >
          A minimum of
          {{ $v.values.password.$params.minLength.min }} characters is required
          here.
        </div>
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
import {
  maxLength,
  minLength,
  required,
  sameAs,
} from 'vuelidate/lib/validators'

import form from '@baserow/modules/core/mixins/form'

export default {
  name: 'ChangePasswordForm',
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
      password: {
        required,
        maxLength: maxLength(256),
        minLength: minLength(8),
      },
      passwordConfirm: {
        sameAsPassword: sameAs('password'),
      },
    },
  },
}
</script>
