<template>
  <div>
    <div class="auth__logo">
      <nuxt-link :to="{ name: 'index' }">
        <img src="@baserow/modules/core/static/img/logo.svg" alt="" />
      </nuxt-link>
    </div>
    <div class="auth__head">
      <h1 class="auth__head-title">
        {{ $t('login.title') }}
      </h1>
      <LangPicker />
    </div>
    <div
      v-if="loginButtons.length > 0"
      class="auth-provider-buttons auth-provider-buttons--border-bottom"
      :class="{ 'auth-provider-buttons--small': smallLoginButtons }"
    >
      <div v-for="loginButton in loginButtons" :key="loginButton.redirect_url">
        <component
          :is="getLoginButtonComponent(loginButton)"
          :redirect-url="loginButton.redirect_url"
          :name="loginButton.name"
          :icon="getLoginButtonIcon(loginButton)"
          :small="smallLoginButtons"
        >
        </component>
      </div>
    </div>
    <div v-else class="auth-provider-buttons__empty-space"></div>
    <AuthLogin :invitation="invitation" @success="success"> </AuthLogin>
    <div>
      <ul class="auth__action-links">
        <li v-for="loginAction in loginActions" :key="loginAction.name">
          <component
            :is="getLoginActionComponent(loginAction)"
            :options="loginAction"
          >
          </component>
        </li>
        <li v-if="settings.allow_reset_password">
          <nuxt-link :to="{ name: 'forgot-password' }">
            {{ $t('login.forgotPassword') }}
          </nuxt-link>
        </li>
        <li v-if="settings.allow_new_signups">
          {{ $t('login.signUpText') }}
          <nuxt-link :to="{ name: 'signup' }">
            {{ $t('login.signUp') }}
          </nuxt-link>
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'

import AuthLogin from '@baserow/modules/core/components/auth/AuthLogin'
import groupInvitationToken from '@baserow/modules/core/mixins/groupInvitationToken'
import LangPicker from '@baserow/modules/core/components/LangPicker'
import { isRelativeUrl } from '@baserow/modules/core/utils/url'

export default {
  components: { AuthLogin, LangPicker },
  layout: 'login',
  async asyncData({ redirect, route, app, store }) {
    if (store.getters['settings/get'].show_admin_signup_page === true) {
      redirect('signup')
    }

    // load authentication providers login options to populate the login
    // page with external providers
    await store.dispatch('authProvider/fetchLoginOptions')

    return await groupInvitationToken.asyncData({ route, app })
  },
  head() {
    return {
      title: this.$t('login.title'),
      link: [
        {
          rel: 'canonical',
          href: this.$env.PUBLIC_WEB_FRONTEND_URL + this.$route.path,
        },
      ],
    }
  },
  computed: {
    ...mapGetters({
      settings: 'settings/get',
      loginActions: 'authProvider/getAllLoginActions',
      loginButtons: 'authProvider/getAllLoginButtons',
    }),
    smallLoginButtons() {
      return this.loginButtons.length > 2
    },
  },
  methods: {
    getLoginActionComponent(loginAction) {
      return this.$registry
        .get('authProvider', loginAction.type)
        .getLoginActionComponent()
    },
    getLoginButtonComponent(loginButton) {
      return this.$registry
        .get('authProvider', loginButton.type)
        .getLoginButtonComponent()
    },
    getLoginButtonIcon(loginButton) {
      return this.$registry.get('authProvider', loginButton.type).getIcon()
    },
    success() {
      const { original } = this.$route.query
      if (original && isRelativeUrl(original)) {
        this.$nuxt.$router.push(original)
      } else {
        this.$nuxt.$router.push({ name: 'dashboard' })
      }
    },
  },
}
</script>
