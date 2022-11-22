<template>
  <nuxt-link :to="{ name: 'login-saml', query: query }">
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
    original: {
      type: String,
      required: false,
      default: null,
    },
  },
  computed: {
    query() {
      const q = this.$route.query
      if (!q.original) {
        q.original = this.original
      }
      return q
    },
    redirectUrl() {
      let original = this.original
      if (!original) {
        original = this.$route.query.original
      }
      const redirectUrl = this.options.redirectUrl
      if (original && isRelativeUrl(original)) {
        return redirectUrl + '?original=' + original
      }
      return redirectUrl
    },
  },
}
</script>
