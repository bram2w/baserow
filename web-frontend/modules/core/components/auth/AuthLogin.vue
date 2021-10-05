<template>
  <div>
    <div
      v-if="invitation !== null"
      class="alert alert--simple alert--primary alert--has-icon"
    >
      <div class="alert__icon">
        <i class="fas fa-exclamation"></i>
      </div>
      <div class="alert__title">
        {{ $t('invitationTitle') }}
      </div>
      <i18n path="invitationMessage" tag="p" class="alert__content">
        <template #invitedBy>
          <strong>{{ invitation.invited_by }}</strong>
        </template>
        <template #group>
          <strong>{{ invitation.group }}</strong>
        </template>
      </i18n>
    </div>
    <Error :error="error"></Error>
    <form @submit.prevent="login">
      <div class="control">
        <label class="control__label">{{ $t('field.emailAddress') }}</label>
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
            {{ $t('error.invalidEmail') }}
          </div>
        </div>
      </div>
      <div class="control">
        <label class="control__label">{{ $t('field.password') }}</label>
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
            {{ $t('error.passwordRequired') }}
          </div>
        </div>
      </div>
      <div class="actions">
        <slot></slot>
        <button
          :class="{ 'button--loading': loading }"
          class="button button--large"
          :disabled="loading"
        >
          {{ $t('action.signIn') }}
          <i class="fas fa-lock-open"></i>
        </button>
      </div>
    </form>
  </div>
</template>

<script>
import { required, email } from 'vuelidate/lib/validators'
import error from '@baserow/modules/core/mixins/error'
import GroupService from '@baserow/modules/core/services/group'

export default {
  name: 'AuthLogin',
  mixins: [error],
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
      credentials: {
        email: '',
        password: '',
      },
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

        this.$emit('success')
      } catch (error) {
        if (error.handler) {
          const response = error.handler.response
          // Because the API server does not yet respond with proper error codes we
          // manually have to add the error here.
          if (response && response.status === 400) {
            // In the future we expect the backend to respond with a proper error code
            // to indicate what went wrong.
            if (
              response.data.non_field_errors &&
              response.data.non_field_errors[0] === 'User account is disabled.'
            ) {
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

<i18n>
{
  "en":{
    "error":{
      "passwordRequired": "A password is required.",
      "invalidEmail": "Please enter a valid e-mail address.",
      "disabledAccountTitle": "Account disabled",
      "disabledAccountMessage": "This user account has been disabled.",
      "incorrectCredentialTitle": "Incorrect credentials",
      "incorrectCredentialMessage": "The provided e-mail address or password is incorrect."
    },
    "field":{
      "password": "Password"
    },
    "invitationTitle": "Invitation",
    "invitationMessage": "{invitedBy} has invited you to join {group}."
  },
  "fr": {
    "error":{
      "passwordRequired": "Le mot de passe est obligatoire.",
      "invalidEmail": "Veuillez entrer une adresse électronique valide.",
      "disabledAccountTitle": "Compte désactivé",
      "disabledAccountMessage": "Ce compte utilisateur est desactivé.",
      "incorrectCredentialTitle": "Identifiants incorrects",
      "incorrectCredentialMessage": "L'adresse éléctronique et/ou le mot de passe sont incorrects."
    },
    "field":{
      "password": "Mot de passe"
    },
    "invitationTitle": "Invitation",
    "invitationMessage": "{invitedBy} vous a invité·e à rejoindre le groupe {group}."
  }
}
</i18n>
