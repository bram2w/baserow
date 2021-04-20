<template>
  <div>
    <h1 class="box__title">
      <nuxt-link :to="{ name: 'index' }">
        <img src="@baserow/modules/core/static/img/logo.svg" alt="" />
      </nuxt-link>
    </h1>
    <AuthLogin :invitation="invitation" @success="success">
      <ul class="action__links">
        <li v-if="settings.allow_new_signups">
          <nuxt-link :to="{ name: 'signup' }"> Sign up </nuxt-link>
        </li>
        <li>
          <nuxt-link :to="{ name: 'forgot-password' }">
            Forgot password
          </nuxt-link>
        </li>
      </ul>
    </AuthLogin>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'

import AuthLogin from '@baserow/modules/core/components/auth/AuthLogin'
import groupInvitationToken from '@baserow/modules/core/mixins/groupInvitationToken'

export default {
  components: { AuthLogin },
  mixins: [groupInvitationToken],
  layout: 'login',
  head() {
    return {
      title: 'Login',
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
    }),
  },
  methods: {
    success() {
      const { original } = this.$route.query
      if (original) {
        this.$nuxt.$router.push(original)
      } else {
        this.$nuxt.$router.push({ name: 'dashboard' })
      }
    },
  },
}
</script>
