<template>
  <div>
    <h1 class="box-title">
      <img src="@/static/img/logo.svg" alt="" />
    </h1>
    <div v-if="invalid" class="alert alert-error alert-has-icon">
      <div class="alert-icon">
        <i class="fas fa-exclamation"></i>
      </div>
      <div class="alert-title">Incorrect credentials</div>
      <p class="alert-content">
        The provided e-mail address or password is incorrect.
      </p>
    </div>
    <form @submit.prevent="login">
      <div class="control">
        <label class="control-label">E-mail address</label>
        <div class="control-elements">
          <input
            ref="email"
            v-model="credentials.email"
            :class="{ 'input-error': $v.credentials.email.$error }"
            type="email"
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
            ref="password"
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
      invalid: false,
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
        this.$store
          .dispatch('auth/login', {
            email: this.credentials.email,
            password: this.credentials.password
          })
          .then(() => {
            this.$nuxt.$router.replace({ name: 'app' })
          })
          .catch(() => {
            this.invalid = true
            this.credentials.password = ''
            this.$v.$reset()
            this.$refs.password.focus()
          })
          .then(() => {
            this.loading = false
          })
      }
    }
  }
}
</script>
