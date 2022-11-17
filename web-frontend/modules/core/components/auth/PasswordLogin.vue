<template>
  <div>
    <Alert
      v-if="invitation !== null"
      simple
      type="primary"
      icon="exclamation"
      :title="$t('invitationTitle')"
    >
      <i18n path="invitationMessage" tag="p">
        <template #invitedBy>
          <strong>{{ invitation.invited_by }}</strong>
        </template>
        <template #group>
          <strong>{{ invitation.group }}</strong>
        </template>
      </i18n>
    </Alert>
    <Error :error="error"></Error>
    <form @submit.prevent="login">
      <FormElement :error="fieldHasErrors('email')" class="auth__control">
        <label class="auth__control-label">{{
          $t('field.emailAddress')
        }}</label>
        <div class="control__elements">
          <input
            v-if="invitation !== null"
            ref="email"
            type="email"
            class="input input--large"
            disabled
            :value="values.email"
          />
          <input
            v-else
            ref="email"
            v-model="values.email"
            :class="{ 'input--error': fieldHasErrors('email') }"
            type="email"
            autocomplete="username"
            :placeholder="$t('login.emailPlaceholder')"
            class="input input--large"
            @blur="$v.values.email.$touch()"
          />
          <div class="auth__control-error">
            <div v-if="fieldHasErrors('email')" class="error">
              <i class="fas fa-fw fa-exclamation-triangle"></i>
              {{ $t('error.invalidEmail') }}
            </div>
          </div>
        </div>
      </FormElement>
      <FormElement :error="fieldHasErrors('password')" class="auth__control">
        <label class="auth__control-label">{{ $t('field.password') }}</label>
        <div class="control__elements">
          <input
            ref="password"
            v-model="values.password"
            :class="{
              'input--error': fieldHasErrors('password'),
            }"
            type="password"
            autocomplete="current-password"
            class="input input--large"
            :placeholder="$t('login.passwordPlaceholder')"
            @blur="$v.values.password.$touch()"
          />
          <div class="auth__control-error">
            <div v-if="fieldHasErrors('password')" class="error">
              <i class="fas fa-warning fa-exclamation-triangle"></i>
              {{ $t('error.passwordRequired') }}
            </div>
          </div>
        </div>
      </FormElement>
      <div class="auth__action">
        <button
          :class="{ 'button--loading': loading }"
          class="button button--full-width"
          :disabled="loading"
        >
          {{ $t('action.signIn') }}
        </button>
      </div>
    </form>
  </div>
</template>

<script>
import { required, email } from 'vuelidate/lib/validators'
import form from '@baserow/modules/core/mixins/form'
import error from '@baserow/modules/core/mixins/error'
import GroupService from '@baserow/modules/core/services/group'

export default {
  name: 'PasswordLogin',
  mixins: [form, error],
  props: {
    invitation: {
      required: false,
      validator: (prop) => typeof prop === 'object' || prop === null,
      default: null,
    },
  },
  data() {
    return {
      loading: false,
      values: {
        email: '',
        password: '',
      },
    }
  },
  beforeMount() {
    if (this.invitation !== null) {
      this.values.email = this.invitation.email
    }
  },
  async mounted() {
    if (!this.$env.BASEROW_DISABLE_PUBLIC_URL_CHECK) {
      const publicBackendUrl = new URL(this.$env.PUBLIC_BACKEND_URL)
      if (publicBackendUrl.host !== window.location.host) {
        // If the host of the browser location does not match the PUBLIC_BACKEND_URL
        // then we are probably mis-configured.
        try {
          // Attempt to connect to the backend using the configured PUBLIC_BACKEND_URL
          // just in-case it is actually configured correctly.
          await this.$client.get('_health/')
        } catch (error) {
          const publicBackendUrlWithProto =
            publicBackendUrl.protocol + '//' + publicBackendUrl.host
          const browserWindowUrl = location.protocol + '//' + location.host
          this.showError(
            'Backend URL mis-configuration detected',
            `Cannot connect to the backend at ${publicBackendUrlWithProto}.` +
              ` You visited Baserow at ${browserWindowUrl} ` +
              ' which indicates you have mis-configured the Baserow ' +
              ' BASEROW_PUBLIC_URL or PUBLIC_BACKEND_URL environment variables. ' +
              ' Please visit https://baserow.io/docs/tutorials/debugging-connection-issues ' +
              ' on how to fix this error.'
          )
        }
      }
    }
  },
  methods: {
    async login() {
      this.$v.$touch()
      if (this.$v.$invalid) {
        this.focusOnFirstError()
        return
      }

      this.loading = true
      this.hideError()

      try {
        const { email, password } = this.values
        const data = await this.$store.dispatch('auth/login', {
          email,
          password,
        })

        // If there is an invitation we can immediately accept that one after the user
        // successfully signs in.
        if (this.invitation?.email === email) {
          await GroupService(this.$client).acceptInvitation(this.invitation.id)
        }

        this.$i18n.setLocale(data.language)
        this.$emit('success')
      } catch (error) {
        if (error.handler) {
          const response = error.handler.response
          if (response && response.status === 401) {
            if (response.data?.error === 'ERROR_DEACTIVATED_USER') {
              this.showError(
                this.$t('error.disabledAccountTitle'),
                this.$t('error.disabledAccountMessage')
              )
            } else {
              this.showError(
                this.$t('error.incorrectCredentialTitle'),
                this.$t('error.incorrectCredentialMessage')
              )
            }

            this.values.password = ''
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
    values: {
      email: { required, email },
      password: { required },
    },
  },
}
</script>
