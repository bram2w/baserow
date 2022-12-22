<template>
  <div>
    <Login
      :display-header="true"
      :redirect-on-success="true"
      :invitation="invitation"
      :redirect-by-default="redirectByDefault"
    ></Login>
  </div>
</template>

<script>
import Login from '@baserow/modules/core/components/auth/Login'
import groupInvitationToken from '@baserow/modules/core/mixins/groupInvitationToken'

export default {
  components: { Login },
  layout: 'login',
  async asyncData({ app, route, store, redirect }) {
    if (store.getters['settings/get'].show_admin_signup_page === true) {
      return redirect({ name: 'signup' })
    } else if (store.getters['auth/isAuthenticated']) {
      return redirect({ name: 'dashboard' })
    }
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
    redirectByDefault() {
      if (this.$route.query.noredirect === null) {
        return false
      }
      return true
    },
  },
}
</script>
