<template>
  <form @submit.prevent="submit">
    <FormElement :error="fieldHasErrors('name')" class="control">
      <label class="control__label">{{ $t('userForm.fullName') }}</label>
      <div class="control__elements">
        <input
          ref="name"
          v-model="values.name"
          :class="{ 'input--error': fieldHasErrors('name') }"
          type="text"
          class="input input--large"
          :disabled="loading"
          @blur="$v.values.name.$touch()"
        />
        <div v-if="fieldHasErrors('name')" class="error">
          {{ $t('userForm.error.invalidName') }}
        </div>
      </div>
    </FormElement>
    <FormElement :error="fieldHasErrors('username')" class="control">
      <label class="control__label">{{ $t('userForm.email') }}</label>
      <div class="control__elements">
        <input
          ref="email"
          v-model="values.username"
          :class="{ 'input--error': fieldHasErrors('username') }"
          type="text"
          class="input input--large"
          :disabled="loading"
          @blur="$v.values.username.$touch()"
        />
        <div v-show="fieldHasErrors('username')" class="error">
          {{ $t('userForm.error.invalidEmail') }}
        </div>
        <div v-show="values.username !== user.username" class="warning">
          {{ $t('userForm.warning.changeEmail') }}
        </div>
      </div>
    </FormElement>
    <FormElement class="control">
      <label class="control__label">{{ $t('userForm.isActive') }}</label>
      <div class="control__elements">
        <Checkbox v-model="values.is_active" :disabled="loading"></Checkbox>
      </div>
      <div v-show="!values.is_active" class="warning">
        {{ $t('userForm.warning.inactiveUser') }}
      </div>
    </FormElement>
    <FormElement class="control">
      <label class="control__label">{{ $t('premium.user.isStaff') }}</label>
      <div class="control__elements">
        <Checkbox v-model="values.is_staff" :disabled="loading"></Checkbox>
      </div>
      <div v-show="values.is_staff" class="warning">
        {{ $t('userForm.warning.userStaff') }}
      </div>
    </FormElement>
    <div class="actions">
      <slot></slot>
      <div class="align-right">
        <button
          class="button button--large button--primary"
          :class="{ 'button--loading': loading }"
          :disabled="loading"
        >
          {{ $t('action.save') }}
        </button>
      </div>
    </div>
  </form>
</template>

<script>
import { email, maxLength, minLength, required } from 'vuelidate/lib/validators'

import form from '@baserow/modules/core/mixins/form'

export default {
  name: 'UserForm',
  mixins: [form],
  props: {
    user: {
      type: Object,
      required: true,
    },
    loading: {
      type: Boolean,
      required: true,
    },
  },
  data() {
    return {
      allowedValues: ['username', 'name', 'is_active', 'is_staff'],
      values: {
        username: '',
        name: '',
        is_active: '',
        is_staff: '',
      },
    }
  },
  validations: {
    values: {
      name: { required, minLength: minLength(2), maxLength: maxLength(150) },
      username: { required, email },
    },
  },
}
</script>
