<template>
  <div>
    <div
      v-if="invitation !== null"
      class="alert alert--simple alert--primary alert--has-icon"
    >
      <div class="alert__icon">
        <i class="fas fa-exclamation"></i>
      </div>
      <div class="alert__title">{{ $t('invitationTitle') }}</div>
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
    <form @submit.prevent="register">
      <div class="control">
        <label class="control__label">{{ $t('field.emailAddress') }}</label>
        <div class="control__elements">
          <input
            v-if="invitation !== null"
            ref="email"
            type="email"
            class="input input--large"
            disabled
            :value="account.email"
          />
          <input
            v-else
            ref="email"
            v-model="account.email"
            :class="{ 'input--error': $v.account.email.$error }"
            type="text"
            class="input input--large"
            @blur="$v.account.email.$touch()"
          />
          <div v-if="$v.account.email.$error" class="error">
            {{ $t('error.invalidEmail') }}
          </div>
        </div>
      </div>
      <div class="control">
        <label class="control__label">{{ $t('field.name') }}</label>
        <div class="control__elements">
          <input
            v-model="account.name"
            :class="{ 'input--error': $v.account.name.$error }"
            type="text"
            class="input input--large"
            @blur="$v.account.name.$touch()"
          />
          <div v-if="$v.account.name.$error" class="error">
            {{ $t('error.minMaxLength', { min: 2, max: 150 }) }}
          </div>
        </div>
      </div>
      <div class="control">
        <label class="control__label">{{ $t('field.password') }}</label>
        <div class="control__elements">
          <PasswordInput
            v-model="account.password"
            :validation-state="$v.account.password"
          />
        </div>
      </div>
      <div class="control">
        <label class="control__label">{{ $t('field.passwordRepeat') }}</label>
        <div class="control__elements">
          <input
            v-model="account.passwordConfirm"
            :class="{ 'input--error': $v.account.passwordConfirm.$error }"
            type="password"
            class="input input--large"
            @blur="$v.account.passwordConfirm.$touch()"
          />
          <div v-if="$v.account.passwordConfirm.$error" class="error">
            {{ $t('error.notMatchingPassword') }}
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
          {{ $t('action.signUp') }}
          <i class="fas fa-user-plus"></i>
        </button>
      </div>
    </form>
  </div>
</template>

<script>
import {
  email,
  maxLength,
  minLength,
  required,
  sameAs,
} from 'vuelidate/lib/validators'
import { ResponseErrorMessage } from '@baserow/modules/core/plugins/clientHandler'
import error from '@baserow/modules/core/mixins/error'
import PasswordInput from '@baserow/modules/core/components/helpers/PasswordInput'
import { passwordValidation } from '@baserow/modules/core/validators'

export default {
  name: 'AuthRegister',
  components: { PasswordInput },
  mixins: [error],
  props: {
    invitation: {
      required: false,
      validator: (prop) => typeof prop === 'object' || prop === null,
      default: null,
    },
    template: {
      required: false,
      validator: (prop) => typeof prop === 'object' || prop === null,
      default: null,
    },
  },
  data() {
    return {
      loading: false,
      account: {
        email: '',
        name: '',
        password: '',
        passwordConfirm: '',
      },
    }
  },
  beforeMount() {
    if (this.invitation !== null) {
      this.account.email = this.invitation.email
    }
  },
  methods: {
    async register() {
      this.$v.$touch()
      if (this.$v.$invalid) {
        return
      }

      this.loading = true
      this.hideError()

      try {
        const values = {
          name: this.account.name,
          email: this.account.email,
          password: this.account.password,
          language: this.$i18n.locale,
        }

        // If there is a valid invitation we can add the group invitation token to the
        // action parameters so that is can be passed along when signing up. That makes
        // the user accept the group invitation without creating a new group for the
        // user.
        if (this.invitation !== null) {
          values.groupInvitationToken = this.$route.query.groupInvitationToken
        }

        // If a template is provided, we can add that id to the parameters so that the
        // template will be installed right while creating the account. This is going
        // to done instead of the default example template.
        if (this.template !== null) {
          values.templateId = this.template.id
        }

        await this.$store.dispatch('auth/register', values)
        Object.values(this.$registry.getAll('plugin')).forEach((plugin) => {
          plugin.userCreated(this.account, this)
        })

        this.$emit('success')
      } catch (error) {
        this.loading = false
        this.handleError(error, 'signup', {
          ERROR_EMAIL_ALREADY_EXISTS: new ResponseErrorMessage(
            this.$t('error.alreadyExistsTitle'),
            this.$t('error.alreadyExistsMessage')
          ),
        })
      }
    },
  },
  validations: {
    account: {
      email: { required, email },
      name: {
        required,
        minLength: minLength(2),
        maxLength: maxLength(150),
      },
      password: passwordValidation,
      passwordConfirm: {
        sameAsPassword: sameAs('password'),
      },
    },
  },
}
</script>

<i18n>
{
  "en":{
    "error":{
      "alreadyExistsTitle": "User already exists",
      "alreadyExistsMessage": "A user with the provided e-mail address already exists."
    },
    "field":{
      "language": "Language",
      "emailAddress": "E-mail address",
      "name":"Your name",
      "password": "Password",
      "passwordRepeat":"Repeat password"
    },
    "invitationTitle": "Invitation",
    "invitationMessage": "{invitedBy} has invited you to join {group}."
  },
  "fr": {
    "error":{
      "alreadyExistsTitle": "l'Utilisateur existe déjà",
      "alreadyExistsMessage": "Un utilisateur avec la même adresse électronique existe déjà."
    },
    "field":{
      "language": "Langue",
      "emailAddress": "Adresse électronique",
      "name":"Votre nom",
      "password": "Mot de passe",
      "passwordRepeat":"Répetez votre mot de passe"
    },
    "invitationTitle": "Invitation",
    "invitationMessage": "{invitedBy} vous a invité·e à rejoindre le groupe {group}."
  }
}
</i18n>
