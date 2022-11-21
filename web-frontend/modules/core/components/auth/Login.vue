<template>
  <div>
    <div v-if="displayHeader">
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
    </div>
    <LoginButtons
      show-border="bottom"
      :hide-if-no-buttons="loginButtonsCompact"
      :invitation="invitation"
      :original="original"
    />
    <PasswordLogin :invitation="invitation" @success="success"> </PasswordLogin>
    <LoginActions :invitation="invitation" :original="original">
      <li v-if="settings.allow_reset_password">
        <nuxt-link :to="{ name: 'forgot-password' }">
          {{ $t('login.forgotPassword') }}
        </nuxt-link>
      </li>
      <li v-if="settings.allow_new_signups">
        <slot name="signup">
          {{ $t('login.signUpText') }}
          <nuxt-link :to="{ name: 'signup' }">
            {{ $t('login.signUp') }}
          </nuxt-link>
        </slot>
      </li>
    </LoginActions>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'

import LoginButtons from '@baserow/modules/core/components/auth/LoginButtons'
import LoginActions from '@baserow/modules/core/components/auth/LoginActions'
import PasswordLogin from '@baserow/modules/core/components/auth/PasswordLogin'
import LangPicker from '@baserow/modules/core/components/LangPicker'
import { isRelativeUrl } from '@baserow/modules/core/utils/url'

export default {
  components: { PasswordLogin, LoginButtons, LangPicker, LoginActions },
  props: {
    original: {
      type: String,
      required: false,
      default: null,
    },
    redirectOnSuccess: {
      type: Boolean,
      required: false,
      default: true,
    },
    displayHeader: {
      type: Boolean,
      required: false,
      default: true,
    },
    invitation: {
      required: false,
      validator: (prop) => typeof prop === 'object' || prop === null,
      default: null,
    },
    loginButtonsCompact: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  computed: {
    ...mapGetters({
      settings: 'settings/get',
      loginActions: 'authProvider/getAllLoginActions',
      loginButtons: 'authProvider/getAllLoginButtons',
    }),
    computedOriginal() {
      let original = this.original
      if (!original) {
        original = this.$route.query.original
      }
      return original
    },
  },
  methods: {
    success() {
      if (this.redirectOnSuccess) {
        const original = this.computedOriginal
        if (original && isRelativeUrl(original)) {
          this.$nuxt.$router.push(original)
        } else {
          this.$nuxt.$router.push({ name: 'dashboard' })
        }
      }
      this.$emit('success')
    },
  },
}
</script>
