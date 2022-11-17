<template>
  <div
    class="auth-provider-buttons"
    :class="{
      'auth-provider-buttons--small': showSmallLoginButtons,
      'auth-provider-buttons--border-bottom':
        loginButtons.length > 0 && showBorder === 'bottom',
      'auth-provider-buttons--border-top':
        loginButtons.length > 0 && showBorder === 'top',
      'auth-provider-buttons__no-buttons': loginButtons.length === 0,
      'auth-provider-buttons__no-buttons--hide':
        loginButtons.length === 0 && hideIfNoButtons === true,
    }"
  >
    <div v-for="loginButton in loginButtons" :key="loginButton.redirect_url">
      <component
        :is="getLoginButtonComponent(loginButton)"
        :redirect-url="addOriginalParamToUrl(loginButton.redirect_url)"
        :name="loginButton.name"
        :icon="getLoginButtonIcon(loginButton)"
        :small="showSmallLoginButtons"
        :invitation="invitation"
      >
      </component>
    </div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import { isRelativeUrl } from '@baserow/modules/core/utils/url'

export default {
  name: 'LoginButtons',
  props: {
    original: {
      type: String,
      required: false,
      default: null,
    },
    showBorder: {
      type: String,
      validate: (value) => ['top', 'bottom', 'none'].includes(value),
      default: 'none',
    },
    hideIfNoButtons: {
      type: Boolean,
      default: false,
    },
    invitation: {
      required: false,
      validator: (prop) => typeof prop === 'object' || prop === null,
      default: null,
    },
  },
  computed: {
    ...mapGetters({
      loginButtons: 'authProvider/getAllLoginButtons',
    }),
    showSmallLoginButtons() {
      return this.loginButtons.length > 2
    },
    computedOriginal() {
      let original = this.original
      if (!original) {
        original = this.$route.query.original
      }
      return original
    },
  },
  methods: {
    getLoginButtonComponent(loginButton) {
      return this.$registry
        .get('authProvider', loginButton.type)
        .getLoginButtonComponent()
    },
    getLoginButtonIcon(loginButton) {
      return this.$registry.get('authProvider', loginButton.type).getIcon()
    },
    addOriginalParamToUrl(url) {
      const original = this.computedOriginal
      if (original && isRelativeUrl(original)) {
        const parsedUrl = new URL(url)
        parsedUrl.searchParams.append('original', original)
        return parsedUrl.toString()
      } else {
        return url
      }
    },
  },
}
</script>
