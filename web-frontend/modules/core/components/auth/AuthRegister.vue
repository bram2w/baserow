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
    <form @submit.prevent="register">
      <div class="auth__control">
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
            :value="account.email"
          />
          <input
            v-else
            ref="email"
            v-model="account.email"
            :class="{ 'input--error': $v.account.email.$error }"
            type="text"
            autocomplete="username"
            class="input input--large"
            :placeholder="$t('signup.emailPlaceholder')"
            @blur="$v.account.email.$touch()"
          />
          <div class="auth__control-error">
            <div v-if="$v.account.email.$error" class="error">
              <i class="fas fa-warning fa-exclamation-triangle"></i>
              {{ $t('error.invalidEmail') }}
            </div>
          </div>
        </div>
      </div>
      <div class="auth__control">
        <label class="auth__control-label">{{ $t('field.name') }}</label>
        <div class="control__elements">
          <input
            v-model="account.name"
            :class="{ 'input--error': $v.account.name.$error }"
            type="text"
            class="input input--large"
            :placeholder="$t('signup.namePlaceholder')"
            @blur="$v.account.name.$touch()"
          />
          <div class="auth__control-error">
            <div v-if="$v.account.name.$error" class="error">
              <i class="fas fa-warning fa-exclamation-triangle"></i>
              {{ $t('error.minMaxLength', { min: 2, max: 150 }) }}
            </div>
          </div>
        </div>
      </div>
      <div class="auth__control">
        <label class="auth__control-label">{{ $t('field.password') }}</label>
        <div class="control__elements">
          <PasswordInput
            v-model="account.password"
            :validation-state="$v.account.password"
            :placeholder="$t('signup.passwordPlaceholder')"
            :error-placeholder-class="'auth__control-error'"
            :show-error-icon="true"
          />
        </div>
      </div>
      <div class="auth__control">
        <label class="auth__control-label">{{
          $t('field.passwordRepeat')
        }}</label>
        <div class="control__elements">
          <input
            v-model="account.passwordConfirm"
            :class="{ 'input--error': $v.account.passwordConfirm.$error }"
            type="password"
            class="input input--large"
            :placeholder="$t('signup.passwordRepeatPlaceholder')"
            @blur="$v.account.passwordConfirm.$touch()"
          />
          <div class="auth__control-error">
            <div v-if="$v.account.passwordConfirm.$error" class="error">
              <i class="fas fa-warning fa-exclamation-triangle"></i>
              {{ $t('error.notMatchingPassword') }}
            </div>
          </div>
        </div>
      </div>
      <component
        :is="component"
        v-for="(component, index) in registerComponents"
        :ref="`register-component-${index}`"
        :key="index"
        @updated-account="updatedAccount"
      ></component>
      <div class="auth__action">
        <button
          :class="{ 'button--loading': loading }"
          class="button button--full-width"
          :disabled="loading"
        >
          {{ $t('action.signUp') }}
        </button>
      </div>
      <slot></slot>
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
  computed: {
    registerComponents() {
      return Object.values(this.$registry.getAll('plugin'))
        .map((plugin) => plugin.getRegisterComponent())
        .filter((component) => component !== null)
    },
  },
  beforeMount() {
    if (this.invitation !== null) {
      this.account.email = this.invitation.email
    }
  },
  methods: {
    async register() {
      this.$v.$touch()
      let registerComponentsValid = true

      for (let i = 0; i < this.registerComponents.length; i++) {
        const ref = this.$refs[`register-component-${i}`][0]
        if (
          Object.prototype.hasOwnProperty.call(ref, 'isValid') &&
          !ref.isValid(this.account)
        ) {
          registerComponentsValid = false
        }
      }

      if (this.$v.$invalid || !registerComponentsValid) {
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
    updatedAccount({ key, value }) {
      this.$set(this.account, key, value)
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
