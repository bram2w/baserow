<template>
  <form
    v-if="hasAtLeastOneLoginOption"
    class="auth-form-element"
    @submit.prevent="onLogin"
  >
    <template v-if="!isAuthenticated">
      <Error :error="error"></Error>
      <FormGroup
        :label="$t('authFormElement.email')"
        :error="
          $v.values.email.$dirty
            ? !$v.values.email.required
              ? $t('error.requiredField')
              : !$v.values.email.email
              ? $t('error.invalidEmail')
              : ''
            : ''
        "
        :autocomplete="isEditMode ? 'off' : ''"
      >
        <input
          v-model="values.email"
          type="text"
          class="input-element"
          :class="{ 'input-element--error': $v.values.email.$error }"
          required
          :placeholder="$t('authFormElement.emailPlaceholder')"
          @blur="$v.values.email.$touch()"
        />
      </FormGroup>
      <FormGroup
        :label="$t('authFormElement.password')"
        :error="
          $v.values.password.$dirty
            ? !$v.values.password.required
              ? $t('error.requiredField')
              : ''
            : ''
        "
      >
        <input
          ref="password"
          v-model="values.password"
          type="password"
          class="input-element"
          :class="{ 'input-element--error': $v.values.password.$error }"
          required
          :placeholder="$t('authFormElement.passwordPlaceholder')"
          @blur="$v.values.password.$touch()"
        />
      </FormGroup>
    </template>
    <button
      class="ab-button ab-button--full-width ab-button--center ab-button--large"
      :class="{
        'loading-spinner': loading,
      }"
      :disabled="$v.$error"
    >
      {{ !isAuthenticated ? $t('action.login') : $t('action.logout') }}
    </button>
  </form>
  <p v-else>{{ $t('authFormElement.selectOrConfigureUserSourceFirst') }}</p>
</template>

<script>
import form from '@baserow/modules/core/mixins/form'
import error from '@baserow/modules/core/mixins/error'
import element from '@baserow/modules/builder/mixins/element'
import { required, email } from 'vuelidate/lib/validators'
import { mapActions } from 'vuex'

export default {
  name: 'AuthFormElement',
  mixins: [element, form, error],
  inject: ['page', 'builder'],
  props: {
    /**
     * @type {Object}
     * @property {number} user_source_id - The id of the user_source.
     */
    element: {
      type: Object,
      required: true,
    },
  },
  data() {
    return { loading: false, values: { email: '', password: '' } }
  },
  computed: {
    selectedUserSource() {
      return this.$store.getters['userSource/getUserSourceById'](
        this.builder,
        this.element.user_source_id
      )
    },
    selectedUserSourceType() {
      if (!this.selectedUserSource) {
        return null
      }
      return this.$registry.get('userSource', this.selectedUserSource.type)
    },
    isAuthenticated() {
      return this.$store.getters['userSourceUser/isAuthenticated']
    },
    loginOptions() {
      if (!this.selectedUserSourceType) {
        return {}
      }
      return this.selectedUserSourceType.getLoginOptions(
        this.selectedUserSource
      )
    },
    hasAtLeastOneLoginOption() {
      return Object.keys(this.loginOptions).length > 0
    },
  },
  watch: {
    userSource: {
      handler(newValue) {
        if (this.element.user_source_id) {
          const found = newValue.find(
            ({ id }) => id === this.element.user_source_id
          )
          if (!found) {
            // If the user_source has been removed we need to update the element
            this.actionForceUpdateElement({
              page: this.page,
              element: this.element,
              values: { user_source_id: null },
            })
          }
        }
      },
    },
  },
  methods: {
    ...mapActions({
      actionForceUpdateElement: 'element/forceUpdate',
    }),
    async onLogin(event) {
      if (this.isAuthenticated) {
        this.$store.dispatch('userSourceUser/logoff')
      } else {
        this.$v.$touch()
        if (this.$v.$invalid) {
          this.focusOnFirstError()
          return
        }
        this.loading = true
        this.hideError()
        try {
          await this.$store.dispatch('userSourceUser/authenticate', {
            userSource: this.selectedUserSource,
            credentials: {
              email: this.values.email,
              password: this.values.password,
            },
            setCookie: this.mode === 'public',
          })
          this.values.password = ''
          this.values.email = ''
          this.$v.$reset()
        } catch (error) {
          if (error.handler) {
            const response = error.handler.response
            if (response && response.status === 401) {
              this.values.password = ''
              this.$v.$reset()
              this.$refs.password.focus()

              if (response.data?.error === 'ERROR_INVALID_CREDENTIALS') {
                this.showError(
                  this.$t('error.incorrectCredentialTitle'),
                  this.$t('error.incorrectCredentialMessage')
                )
              }
            } else {
              const message = error.handler.getMessage('login')
              this.showError(message)
            }

            error.handler.handled()
          } else {
            throw error
          }
        }
        this.loading = false
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
