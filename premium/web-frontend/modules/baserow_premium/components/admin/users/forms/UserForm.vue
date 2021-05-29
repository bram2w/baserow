<template>
  <form @submit.prevent="submit">
    <div class="control">
      <label class="control__label">Full name</label>
      <div class="control__elements">
        <input
          ref="name"
          v-model="values.name"
          :class="{ 'input--error': $v.values.name.$error }"
          type="text"
          class="input input--large"
          :disabled="loading"
          @blur="$v.values.name.$touch()"
        />
        <div v-if="$v.values.name.$error" class="error">
          Please enter a valid full name, it must be longer than 2 letters and
          less than 30.
        </div>
      </div>
    </div>
    <label class="control__label">Email</label>
    <div class="control">
      <div class="control__elements">
        <input
          ref="email"
          v-model="values.username"
          :class="{ 'input--error': $v.values.username.$error }"
          type="text"
          class="input input--large"
          :disabled="loading"
          @blur="$v.values.username.$touch()"
        />
        <div v-show="$v.values.username.$error" class="error">
          Please enter a valid e-mail address.
        </div>
        <div v-show="values.username !== user.username" class="warning">
          Changing this users email address means when they sign in they must
          use the new email address to do so. This must be communicated with
          that user.
        </div>
      </div>
    </div>
    <label class="control__label">Is active</label>
    <div class="control">
      <div class="control__elements">
        <Checkbox v-model="values.is_active" :disabled="loading"></Checkbox>
      </div>
      <div v-show="!values.is_active" class="warning">
        When a user is marked as inactive they are prevented from signing in.
      </div>
    </div>
    <label class="control__label">Is staff</label>
    <div class="control">
      <div class="control__elements">
        <Checkbox v-model="values.is_staff" :disabled="loading"></Checkbox>
      </div>
      <div v-show="values.is_staff" class="warning">
        Making the user staff gives them admin access to all users, all groups
        and the ability to revoke your own staff permissions.
      </div>
    </div>
    <div class="actions">
      <slot></slot>
      <div class="align-right">
        <button
          class="button button--large button--primary"
          :class="{ 'button--loading': loading }"
          :disabled="loading"
        >
          Save
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
      name: { required, minLength: minLength(2), maxLength: maxLength(30) },
      username: { required, email },
    },
  },
}
</script>
