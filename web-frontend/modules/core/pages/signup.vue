<template>
  <div>
    <div class="auth__logo">
      <nuxt-link :to="{ name: 'index' }">
        <img src="@baserow/modules/core/static/img/logo.svg" alt="" />
      </nuxt-link>
    </div>
    <div class="auth__head auth__head--more-margin">
      <h1 class="auth__head-title">
        {{ $t('signup.title') }}
      </h1>
      <LangPicker />
    </div>
    <template v-if="shouldShowAdminSignupPage">
      <Alert :title="$t('signup.requireFirstUser')">{{
        $t('signup.requireFirstUserMessage')
      }}</Alert>
    </template>
    <template v-if="!isSignupEnabled">
      <Alert
        simple
        type="error"
        icon="exclamation"
        :title="$t('signup.disabled')"
        >{{ $t('signup.disabledMessage') }}</Alert
      >
      <nuxt-link :to="{ name: 'login' }" class="button button--full-width">
        {{ $t('action.backToLogin') }}
      </nuxt-link>
    </template>
    <template v-else>
      <PasswordRegister
        v-if="afterSignupStep < 0"
        :invitation="invitation"
        @success="next"
      >
        <LoginButtons
          show-border="top"
          :hide-if-no-buttons="true"
          :invitation="invitation"
        />
        <LoginActions
          v-if="!shouldShowAdminSignupPage"
          :invitation="invitation"
        >
          <li>
            {{ $t('signup.loginText') }}
            <nuxt-link :to="{ name: 'login' }">
              {{ $t('action.login') }}
            </nuxt-link>
          </li>
        </LoginActions>
      </PasswordRegister>
      <component
        :is="afterSignupStepComponents[afterSignupStep]"
        v-else
        @success="next"
      ></component>
    </template>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import PasswordRegister from '@baserow/modules/core/components/auth/PasswordRegister'
import LangPicker from '@baserow/modules/core/components/LangPicker'
import LoginButtons from '@baserow/modules/core/components/auth/LoginButtons'
import LoginActions from '@baserow/modules/core/components/auth/LoginActions'
import groupInvitationToken from '@baserow/modules/core/mixins/groupInvitationToken'

export default {
  components: { PasswordRegister, LangPicker, LoginButtons, LoginActions },
  layout: 'login',
  async asyncData({ app, route, store, redirect }) {
    if (store.getters['auth/isAuthenticated']) {
      return redirect({ name: 'dashboard' })
    }
    await store.dispatch('authProvider/fetchLoginOptions')
    return await groupInvitationToken.asyncData({ route, app })
  },
  data() {
    return {
      afterSignupStep: -1,
    }
  },
  head() {
    return {
      title: this.$t('signup.headTitle'),
    }
  },
  computed: {
    isSignupEnabled() {
      return (
        this.settings.allow_new_signups ||
        (this.settings.allow_signups_via_group_invitations &&
          this.invitation?.id)
      )
    },
    shouldShowAdminSignupPage() {
      return this.settings.show_admin_signup_page
    },
    afterSignupStepComponents() {
      return Object.values(this.$registry.getAll('plugin'))
        .reduce((components, plugin) => {
          components = components.concat(plugin.getAfterSignupStepComponent())
          return components
        }, [])
        .filter((component) => component !== null)
    },
    ...mapGetters({
      settings: 'settings/get',
      loginActions: 'authProvider/getAllLoginActions',
    }),
  },
  methods: {
    next() {
      if (this.afterSignupStep + 1 < this.afterSignupStepComponents.length) {
        this.afterSignupStep++
      } else {
        this.$nuxt.$router.push({ name: 'dashboard' }, () => {
          this.$store.dispatch('settings/hideAdminSignupPage')
        })
      }
    },
  },
}
</script>
