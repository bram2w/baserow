<template>
  <div>
    <EmailNotVerified v-if="displayEmailNotVerified" :email="emailToVerify">
    </EmailNotVerified>
    <template v-if="!displayEmailNotVerified">
      <div class="auth__logo">
        <nuxt-link :to="{ name: 'index' }">
          <Logo />
        </nuxt-link>
      </div>
      <div class="auth__head auth__head--more-margin">
        <h1 class="auth__head-title">
          {{ $t('signup.title') }}
        </h1>
        <LangPicker />
      </div>
      <template v-if="shouldShowAdminSignupPage">
        <Alert>
          <template #title>{{ $t('signup.requireFirstUser') }}</template>
          <p>{{ $t('signup.requireFirstUserMessage') }}</p></Alert
        >
      </template>
      <template v-if="!isSignupEnabled">
        <Alert type="error">
          <template #title>{{ $t('signup.disabled') }}</template>
          <p>{{ $t('signup.disabledMessage') }}</p></Alert
        >
        <nuxt-link :to="{ name: 'login' }" class="button button--full-width">
          {{ $t('action.backToLogin') }}
        </nuxt-link>
      </template>
      <template v-else>
        <PasswordRegister
          v-if="afterSignupStep < 0 && passwordLoginEnabled"
          :invitation="invitation"
          @success="next"
        >
        </PasswordRegister>
        <LoginButtons
          v-if="afterSignupStep < 0"
          show-border="top"
          :hide-if-no-buttons="true"
          :invitation="invitation"
        />
        <LoginActions
          v-if="!shouldShowAdminSignupPage && afterSignupStep < 0"
          :invitation="invitation"
        >
          <li>
            {{ $t('signup.loginText') }}
            <nuxt-link :to="{ name: 'login' }">
              {{ $t('action.login') }}
            </nuxt-link>
          </li>
        </LoginActions>
        <component
          :is="afterSignupStepComponents[afterSignupStep]"
          @success="next"
        ></component>
      </template>
    </template>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import PasswordRegister from '@baserow/modules/core/components/auth/PasswordRegister'
import LangPicker from '@baserow/modules/core/components/LangPicker'
import LoginButtons from '@baserow/modules/core/components/auth/LoginButtons'
import LoginActions from '@baserow/modules/core/components/auth/LoginActions'
import workspaceInvitationToken from '@baserow/modules/core/mixins/workspaceInvitationToken'
import { EMAIL_VERIFICATION_OPTIONS } from '@baserow/modules/core/enums'
import EmailNotVerified from '@baserow/modules/core/components/auth/EmailNotVerified.vue'

export default {
  components: {
    PasswordRegister,
    LangPicker,
    LoginButtons,
    LoginActions,
    EmailNotVerified,
  },
  layout: 'login',
  async asyncData({ app, route, store, redirect }) {
    if (store.getters['auth/isAuthenticated']) {
      return redirect({ name: 'dashboard' })
    }
    await store.dispatch('authProvider/fetchLoginOptions')
    return await workspaceInvitationToken.asyncData({ route, app })
  },
  data() {
    return {
      afterSignupStep: -1,
      displayEmailNotVerified: false,
      emailToVerify: null,
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
        (this.settings.allow_signups_via_workspace_invitations &&
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
      passwordLoginEnabled: 'authProvider/getPasswordLoginEnabled',
    }),
  },
  methods: {
    next(params) {
      if (params?.email) {
        this.emailToVerify = params.email
      }

      if (this.afterSignupStep + 1 < this.afterSignupStepComponents.length) {
        this.afterSignupStep++
      } else if (
        this.emailToVerify &&
        this.settings.email_verification ===
          EMAIL_VERIFICATION_OPTIONS.ENFORCED &&
        !this.$route.query.workspaceInvitationToken
      ) {
        this.displayEmailNotVerified = true
      } else {
        this.$nuxt.$router.push({ name: 'dashboard' }, () => {
          this.$store.dispatch('settings/hideAdminSignupPage')
        })
      }
    },
  },
}
</script>
