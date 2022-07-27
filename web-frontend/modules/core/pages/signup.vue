<template>
  <div>
    <div class="box__head">
      <h1 class="box__head-title">
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
      <nuxt-link
        :to="{ name: 'login' }"
        class="button button--large button--primary"
      >
        <i class="fas fa-arrow-left"></i>
        {{ $t('action.backToLogin') }}
      </nuxt-link>
    </template>
    <AuthRegister v-else :invitation="invitation" @success="success">
      <ul v-if="!shouldShowAdminSignupPage" class="action__links">
        <li>
          <nuxt-link :to="{ name: 'login' }">
            <i class="fas fa-arrow-left"></i>
            {{ $t('action.back') }}
          </nuxt-link>
        </li>
      </ul>
    </AuthRegister>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'

import groupInvitationToken from '@baserow/modules/core/mixins/groupInvitationToken'
import AuthRegister from '@baserow/modules/core/components/auth/AuthRegister'
import LangPicker from '@baserow/modules/core/components/LangPicker'

export default {
  components: { AuthRegister, LangPicker },
  mixins: [groupInvitationToken],
  layout: 'login',
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
    ...mapGetters({
      settings: 'settings/get',
    }),
  },
  methods: {
    success() {
      this.$nuxt.$router.push({ name: 'dashboard' }, () => {
        this.$store.dispatch('settings/hideAdminSignupPage')
      })
    },
  },
}
</script>
