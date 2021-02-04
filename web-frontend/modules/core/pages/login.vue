<template>
  <div>
    <h1 class="box__title">
      <nuxt-link :to="{ name: 'index' }">
        <img src="@baserow/modules/core/static/img/logo.svg" alt="" />
      </nuxt-link>
    </h1>
    <div
      v-if="invitation !== null"
      class="alert alert--simple alert-primary alert--has-icon"
    >
      <div class="alert__icon">
        <i class="fas fa-exclamation"></i>
      </div>
      <div class="alert__title">Invitation</div>
      <p class="alert__content">
        <strong>{{ invitation.invited_by }}</strong> has invited you to join
        <strong>{{ invitation.group }}</strong
        >.
      </p>
    </div>
    <Error :error="error"></Error>
    <form @submit.prevent="login">
      <div class="control">
        <label class="control__label">E-mail address</label>
        <div class="control__elements">
          <input
            v-if="invitation !== null"
            ref="email"
            type="email"
            class="input input--large"
            disabled
            :value="credentials.email"
          />
          <input
            v-else
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
            <nuxt-link :to="{ name: 'signup' }"> Sign up </nuxt-link>
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
import groupInvitationToken from '@baserow/modules/core/mixins/groupInvitationToken'
import GroupService from '@baserow/modules/core/services/group'

export default {
  mixins: [error, groupInvitationToken],
  layout: 'login',
  data() {
    return {
      loading: false,
      credentials: {
        email: '',
        password: '',
      },
    }
  },
  head() {
    return {
      title: 'Login',
      link: [
        {
          rel: 'canonical',
          href: this.$env.PUBLIC_WEB_FRONTEND_URL + this.$route.path,
        },
      ],
    }
  },
  beforeMount() {
    if (this.invitation !== null) {
      this.credentials.email = this.invitation.email
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

        // If there is an invitation we can immediately accept that one after the user
        // successfully signs in.
        if (
          this.invitation !== null &&
          this.invitation.email === this.credentials.email
        ) {
          await GroupService(this.$client).acceptInvitation(this.invitation.id)
        }

        const { original } = this.$route.query
        if (original) {
          this.$nuxt.$router.push(original)
        } else {
          this.$nuxt.$router.push({ name: 'dashboard' })
        }
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
  validations: {
    credentials: {
      email: { required, email },
      password: { required },
    },
  },
}
</script>
