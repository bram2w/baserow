<template>
  <div>
    <h1 class="box__title">
      <nuxt-link :to="{ name: 'index' }">
        <img src="@baserow/modules/core/static/img/logo.svg" alt="" />
      </nuxt-link>
    </h1>
    <Error :error="error"></Error>
    <form @submit.prevent="login">
      <div class="control">
        <label class="control__label">E-mail address</label>
        <div class="control__elements">
          <input
            ref="email"
            v-model="credentials.email"
            :class="{ 'input--error': $v.credentials.email.$error }"
            type="email"
            class="input input--large"
            @blur="$v.credentials.email.$touch()"
          />
          <div v-if="$v.credentials.email.$error" class="error">
            Please enter a valid e-mail address.
          </div>
        </div>
      </div>
      <div class="control">
        <label class="control__label">Password</label>
        <div class="control__elements">
          <input
            ref="password"
            v-model="credentials.password"
            :class="{ 'input--error': $v.credentials.password.$error }"
            type="password"
            class="input input--large"
            @blur="$v.credentials.password.$touch()"
          />
          <div v-if="$v.credentials.password.$error" class="error">
            A password is required.
          </div>
        </div>
      </div>
      <div class="actions">
        <ul class="action__links">
          <li>
            <nuxt-link :to="{ name: 'signup' }">
              Sign up
            </nuxt-link>
          </li>
          <li>
            <nuxt-link :to="{ name: 'forgot-password' }">
              Forgot password
            </nuxt-link>
          </li>
        </ul>
        <button
          :class="{ 'button--loading': loading }"
          class="button button--large"
          :disabled="loading"
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
import error from '@baserow/modules/core/mixins/error'

export default {
  layout: 'login',
  mixins: [error],
  data() {
    return {
      loading: false,
      credentials: {
        email: '',
        password: '',
      },
    }
  },
  methods: {
    async login() {
      this.$v.$touch()
      if (this.$v.$invalid) {
        return
      }

      this.loading = true
      this.hideError()

      try {
        await this.$store.dispatch('auth/login', {
          email: this.credentials.email,
          password: this.credentials.password,
        })
        this.$nuxt.$router.push({ name: 'dashboard' })
      } catch (error) {
        if (error.handler) {
          const response = error.handler.response
          // Because the API server does not yet respond with proper error codes we
          // manually have to add the error here.
          if (response && response.status === 400) {
            this.showError(
              'Incorrect credentials',
              'The provided e-mail address or password is ' + 'incorrect.'
            )
            this.credentials.password = ''
            this.$v.$reset()
            this.$refs.password.focus()
          } else {
            const message = error.handler.getMessage('login')
            this.showError(message)
          }

          this.loading = false
          error.handler.handled()
        } else {
          throw error
        }
      }
    },
  },
  head() {
    return {
      title: 'Login',
    }
  },
  validations: {
    credentials: {
      email: { required, email },
      password: { required },
    },
  },
}
</script>
