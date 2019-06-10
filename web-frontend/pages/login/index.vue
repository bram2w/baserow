<template>
  <div>
    <h1 class="box-title">
      <img src="@/static/img/logo.svg" alt="" />
    </h1>
    <form @submit.prevent="login">
      <div class="control">
        <label class="control-label">E-mail address</label>
        <div class="control-elements">
          <input
            v-model="credentials.email"
            :class="{ 'input-error': $v.credentials.email.$error }"
            type="text"
            class="input input-large"
            @blur="$v.credentials.email.$touch()"
          />
          <div v-if="$v.credentials.email.$error" class="error">
            Please enter a valid e-mail address.
          </div>
        </div>
      </div>
      <div class="control">
        <label class="control-label">Password</label>
        <div class="control-elements">
          <input
            v-model="credentials.password"
            :class="{ 'input-error': $v.credentials.password.$error }"
            type="password"
            class="input input-large"
            @blur="$v.credentials.password.$touch()"
          />
          <div v-if="$v.credentials.password.$error" class="error">
            A password is required.
          </div>
        </div>
      </div>
      <div class="actions">
        <ul class="action-links">
          <li>
            <nuxt-link :to="{ name: 'login-signup' }">
              Sign up
            </nuxt-link>
          </li>
        </ul>
        <button
          :class="{ 'button-loading': loading }"
          class="button button-large"
        >
          Sign in
          <i class="fas fa-lock-open"></i>
        </button>
      </div>
    </form>
  </div>
</template>

<script>
import { required, email } from 'vuelidate/lib/validators'

export default {
  layout: 'login',
  head() {
    return {
      title: 'Login'
    }
  },
  data() {
    return {
      loading: false,
      credentials: {
        email: '',
        password: ''
      }
    }
  },
  validations: {
    credentials: {
      email: { required, email },
      password: { required }
    }
  },
  methods: {
    login() {
      this.$v.$touch()
      if (!this.$v.$invalid) {
        this.loading = true
      }
    }
  }
}
</script>
