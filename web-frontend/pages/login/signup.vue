<template>
  <div>
    <h1 class="box-title">Sign up</h1>
    <div
      v-if="error == 'ERROR_ALREADY_EXISTS'"
      class="alert alert-error alert-has-icon"
    >
      <div class="alert-icon">
        <i class="fas fa-exclamation"></i>
      </div>
      <div class="alert-title">User already exists</div>
      <p class="alert-content">
        A user with the provided e-mail address already exists.
      </p>
    </div>
    <form @submit.prevent="register">
      <div class="control">
        <label class="control-label">E-mail address</label>
        <div class="control-elements">
          <input
            v-model="account.email"
            :class="{ 'input-error': $v.account.email.$error }"
            type="text"
            class="input input-large"
            @blur="$v.account.email.$touch()"
          />
          <div v-if="$v.account.email.$error" class="error">
            Please enter a valid e-mail address.
          </div>
        </div>
      </div>
      <div class="control">
        <label class="control-label">Your name</label>
        <div class="control-elements">
          <input
            v-model="account.name"
            :class="{ 'input-error': $v.account.name.$error }"
            type="text"
            class="input input-large"
            @blur="$v.account.name.$touch()"
          />
          <div v-if="$v.account.name.$error" class="error">
            A minimum of two characters is required here.
          </div>
        </div>
      </div>
      <div class="control">
        <label class="control-label">Password</label>
        <div class="control-elements">
          <input
            v-model="account.password"
            :class="{ 'input-error': $v.account.password.$error }"
            type="password"
            class="input input-large"
            @blur="$v.account.password.$touch()"
          />
          <div v-if="$v.account.password.$error" class="error">
            A password is required.
          </div>
        </div>
      </div>
      <div class="control">
        <label class="control-label">Repeat password</label>
        <div class="control-elements">
          <input
            v-model="account.passwordConfirm"
            :class="{ 'input-error': $v.account.passwordConfirm.$error }"
            type="password"
            class="input input-large"
            @blur="$v.account.passwordConfirm.$touch()"
          />
          <div v-if="$v.account.passwordConfirm.$error" class="error">
            This field must match your password field.
          </div>
        </div>
      </div>
      <div class="actions">
        <ul class="action-links">
          <li>
            <nuxt-link :to="{ name: 'login' }">
              <i class="fas fa-arrow-left"></i>
              Back
            </nuxt-link>
          </li>
        </ul>
        <button
          :class="{ 'button-loading': loading }"
          class="button button-large"
          :disabled="loading"
        >
          Sign up
          <i class="fas fa-user-plus"></i>
        </button>
      </div>
    </form>
  </div>
</template>

<script>
import { required, email, sameAs, minLength } from 'vuelidate/lib/validators'

export default {
  layout: 'login',
  head() {
    return {
      title: 'Create new account'
    }
  },
  validations: {
    account: {
      email: { required, email },
      name: {
        required,
        minLength: minLength(2)
      },
      password: { required },
      passwordConfirm: {
        sameAsPassword: sameAs('password')
      }
    }
  },
  data() {
    return {
      error: '',
      loading: false,
      account: {
        email: '',
        name: '',
        password: '',
        passwordConfirm: ''
      }
    }
  },
  methods: {
    register() {
      this.$v.$touch()
      if (!this.$v.$invalid) {
        this.loading = true
        this.error = ''
        this.$store
          .dispatch('auth/register', {
            name: this.account.name,
            email: this.account.email,
            password: this.account.password
          })
          .then(() => {
            this.$nuxt.$router.replace({ name: 'app' })
          })
          .catch(error => {
            this.error = error.responseError
            this.$v.$reset()
          })
          .then(() => {
            this.loading = false
          })
      }
    }
  }
}
</script>
