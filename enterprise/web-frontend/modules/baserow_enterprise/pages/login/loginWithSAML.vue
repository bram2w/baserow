<template>
  <div>
    <div class="box__head-logo">
      <nuxt-link :to="{ name: 'index' }">
        <img src="@baserow/modules/core/static/img/logo.svg" alt="" />
      </nuxt-link>
    </div>
    <div class="login-box__head">
      <h1 class="box__head-title">
        {{ $t('loginWithSaml.signInWithSaml') }}
      </h1>
    </div>
    <form @submit.prevent="login">
      <FormElement :error="fieldHasErrors('email')" class="login-control">
        <label class="login-control__label">{{
          $t('field.emailAddress')
        }}</label>
        <div class="control__elements">
          <input
            ref="email"
            v-model="values.email"
            :class="{
              'input--error': fieldHasErrors('email') || loginRequestError,
            }"
            type="email"
            :placeholder="$t('login.emailPlaceholder')"
            class="input input--large"
            @input="loginRequestError = null"
            @blur="$v.values.email.$touch()"
          />
          <div class="login-error">
            <div v-if="fieldHasErrors('email')">
              <i class="fas fa-fw fa-exclamation-triangle"></i>
              {{ $t('error.invalidEmail') }}
            </div>
            <div v-else-if="loginRequestError">
              <i class="fas fa-fw fa-exclamation-triangle"></i>
              {{ $t('loginWithSaml.requestError') }}
            </div>
          </div>
        </div>
      </FormElement>
    </form>
    <div class="login-actions">
      <button
        :class="{ 'button--loading': loading }"
        class="button login-button--full-width"
        :disabled="loading"
        @click="login"
      >
        {{ $t('loginWithSaml.continueWithSaml') }}
      </button>
    </div>
    <div class="actions">
      <ul class="action__links">
        <li>
          <nuxt-link :to="{ name: 'login' }">
            <i class="fas fa-arrow-left"></i>
            {{ $t('action.back') }}
          </nuxt-link>
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
import { required, email } from 'vuelidate/lib/validators'
import form from '@baserow/modules/core/mixins/form'
import error from '@baserow/modules/core/mixins/error'
import samlAuthProviderService from '@baserow_enterprise/services/samlAuthProvider'

export default {
  mixins: [form, error],
  layout: 'login',
  async asyncData({ app, redirect, store, route }) {
    if (store.getters['settings/get'].show_admin_signup_page === true) {
      redirect('signup')
    }

    // if this page is accessed directly, load the login options to
    // populate the page with all the authentication providers
    if (!store.getters['authProvider/getLoginOptionsLoaded']) {
      const loginOptions = await store.dispatch(
        'authProvider/fetchLoginOptions'
      )
      if (!loginOptions.saml) {
        return redirect('/login')
      } else if (!loginOptions.saml.domainRequired) {
        const { data } = await samlAuthProviderService(
          app.$client
        ).getSamlLoginUrl({
          original: route.query.original,
        })
        return redirect(data.redirect_url)
      }
    }
  },
  data() {
    return {
      loading: false,
      loginRequestError: false,
      values: {
        email: '',
      },
    }
  },
  methods: {
    async login() {
      this.$v.$touch()
      this.loginRequestError = false
      if (this.$v.$invalid) {
        this.focusOnFirstError()
        return
      }

      this.loading = true
      this.hideError()

      const { original } = this.$route.query
      try {
        const { data } = await samlAuthProviderService(
          this.$client
        ).getSamlLoginUrl({
          email: this.values.email,
          original,
        })
        window.location = data.redirect_url
      } catch (error) {
        this.loginRequestError = true
        this.loading = false
      }
    },
  },
  validations: {
    values: {
      email: { required, email },
    },
  },
}
</script>
