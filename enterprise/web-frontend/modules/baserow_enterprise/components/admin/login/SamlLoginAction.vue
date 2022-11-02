<template>
  <nuxt-link :to="{ name: 'login-saml', query: $route.query }">
    {{ $t('loginWithSaml.signInWithSaml') }}
  </nuxt-link>
</template>

<script>
import { isRelativeUrl } from '@baserow/modules/core/utils/url'

export default {
  name: 'SamlLoginAction',
  props: {
    options: {
      type: Object,
      required: true,
    },
  },
  computed: {
    redirectUrl() {
      const { original } = this.$route.query
      const redirectUrl = this.options.redirectUrl
      if (original && isRelativeUrl(original)) {
        return redirectUrl + '?original=' + original
      }
      return redirectUrl
    },
  },
}
</script>
