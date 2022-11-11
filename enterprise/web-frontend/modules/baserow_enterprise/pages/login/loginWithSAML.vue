<template>
  <div>
    <div v-if="!redirectImmediately">
      <div class="auth__logo">
        <nuxt-link :to="{ name: 'index' }">
          <img src="@baserow/modules/core/static/img/logo.svg" alt="" />
        </nuxt-link>
      </div>
      <div class="auth__head auth__head--more-margin">
        <h1 class="auth__head-title">
          {{ $t('loginWithSaml.signInWithSaml') }}
        </h1>
      </div>
      <form @submit.prevent="login">
        <FormElement :error="fieldHasErrors('email')" class="auth__control">
          <label class="auth__control-label">{{
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
            <div class="auth__control-error">
              <div v-if="fieldHasErrors('email')" class="error">
                <i class="fas fa-fw fa-exclamation-triangle"></i>
                {{ $t('error.invalidEmail') }}
              </div>
              <div v-else-if="loginRequestError" class="error">
                <i class="fas fa-fw fa-exclamation-triangle"></i>
                {{ $t('loginWithSaml.requestError') }}
              </div>
            </div>
          </div>
        </FormElement>
      </form>
      <div class="auth__actions">
        <button
          :class="{ 'button--loading': loading }"
          class="button button--full-width"
          :disabled="loading"
          @click="login"
        >
          {{ $t('loginWithSaml.continueWithSaml') }}
        </button>
      </div>
      <div>
        <ul class="auth__action-links">
          <li>
            {{ $t('loginWithSaml.loginText') }}
            <nuxt-link :to="{ name: 'login' }">
              {{ $t('action.login') }}
            </nuxt-link>
          </li>
        </ul>
      </div>
    </div>
    <div v-else>
      <h2>
        {{ $t('loginWithSaml.redirecting') }}
      </h2>
    </div>
  </div>
</template>

<script>
import decamelize from 'decamelize'
import { required, email } from 'vuelidate/lib/validators'
import form from '@baserow/modules/core/mixins/form'
import error from '@baserow/modules/core/mixins/error'
import groupInvitationToken from '@baserow/modules/core/mixins/groupInvitationToken'
import { SamlAuthProviderType } from '@baserow_enterprise/authProviderTypes'
import samlAuthProviderService from '@baserow_enterprise/services/samlAuthProvider'

export default {
  mixins: [form, error],
  layout: 'login',
  async asyncData({ app, redirect, store, route }) {
    // the SuperUser must create the account using username and password
    if (store.getters['settings/get'].show_admin_signup_page === true) {
      return redirect({ name: 'signup' })
    }

    // if this page is accessed directly, load the login options to
    // populate the page with all the authentication providers
    if (!store.getters['authProvider/getLoginOptionsLoaded']) {
      await store.dispatch('authProvider/fetchLoginOptions')
    }

    const samlLoginOptions = store.getters[
      'authProvider/getLoginOptionsForType'
    ](new SamlAuthProviderType().getType())

    if (!samlLoginOptions) {
      return redirect({ name: 'login', query: route.query }) // no SAML provider enabled
    }

    // in case the email is not necessary or provided via group invitation,
    // redirect the user directly to the SAML provider
    const { invitation } = await groupInvitationToken.asyncData({ route, app })
    if (!samlLoginOptions.domainRequired || invitation?.email) {
      try {
        const { data } = await samlAuthProviderService(
          app.$client
        ).getSamlLoginUrl({
          email: invitation?.email,
          original: route.query.original,
        })
        return { redirectImmediately: true, redirectUrl: data.redirect_url }
      } catch (error) {
        return { values: { email: invitation?.email }, loginRequestError: true }
      }
    }

    return { redirectUrl: samlLoginOptions.redirect_url }
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
  mounted() {
    if (this.redirectImmediately) {
      window.location.href = this.getRedirectUrlWithValidQueryParams(
        this.redirectUrl
      )
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
        window.location = this.getRedirectUrlWithValidQueryParams(
          data.redirect_url
        )
      } catch (error) {
        this.loginRequestError = true
        this.loading = false
      }
    },
    getRedirectUrlWithValidQueryParams(url) {
      const parsedUrl = new URL(url)
      for (const [key, value] of Object.entries(this.$route.query)) {
        if (['language', 'groupInvitationToken'].includes(key)) {
          parsedUrl.searchParams.append(decamelize(key), value)
        }
      }
      return parsedUrl.toString()
    },
  },
  validations: {
    values: {
      email: { required, email },
    },
  },
}
</script>
