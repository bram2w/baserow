<template>
  <div>
    <div
      v-if="invitation !== null"
      class="alert alert--simple alert--primary alert--has-icon"
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
    <form @submit.prevent="register">
      <div class="control">
        <label class="control__label">E-mail address</label>
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
            Please enter a valid e-mail address.
          </div>
        </div>
      </div>
      <div class="control">
        <label class="control__label">Your name</label>
        <div class="control__elements">
          <input
            v-model="account.name"
            :class="{ 'input--error': $v.account.name.$error }"
            type="text"
            class="input input--large"
            @blur="$v.account.name.$touch()"
          />
          <div v-if="$v.account.name.$error" class="error">
            A minimum of two characters is required here.
          </div>
        </div>
      </div>
      <div class="control">
        <label class="control__label">Password</label>
        <div class="control__elements">
          <input
            v-model="account.password"
            :class="{ 'input--error': $v.account.password.$error }"
            type="password"
            class="input input--large"
            @blur="$v.account.password.$touch()"
          />
          <div
            v-if="$v.account.password.$error && !$v.account.password.required"
            class="error"
          >
            A password is required.
          </div>
          <div
            v-if="$v.account.password.$error && !$v.account.password.maxLength"
            class="error"
          >
            A maximum of
            {{ $v.account.password.$params.maxLength.max }} characters is
            allowed here.
          </div>
          <div
            v-if="$v.account.password.$error && !$v.account.password.minLength"
            class="error"
          >
            A minimum of
            {{ $v.account.password.$params.minLength.min }} characters is
            allowed here.
          </div>
        </div>
      </div>
      <div class="control">
        <label class="control__label">Repeat password</label>
        <div class="control__elements">
          <input
            v-model="account.passwordConfirm"
            :class="{ 'input--error': $v.account.passwordConfirm.$error }"
            type="password"
            class="input input--large"
            @blur="$v.account.passwordConfirm.$touch()"
          />
          <div v-if="$v.account.passwordConfirm.$error" class="error">
            This field must match your password field.
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
          Sign up
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

export default {
  name: 'AuthRegister',
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
            'User already exists.',
            'A user with the provided e-mail address already exists.'
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
      },
      password: {
        required,
        maxLength: maxLength(256),
        minLength: minLength(8),
      },
      passwordConfirm: {
        sameAsPassword: sameAs('password'),
      },
    },
  },
}
</script>
