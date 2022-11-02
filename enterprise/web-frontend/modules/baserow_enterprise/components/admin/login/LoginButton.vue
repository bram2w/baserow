<template>
  <div>
    <a
      class="auth-provider-buttons__button"
      :class="{ 'auth-provider-buttons__button--small': small }"
      :href="`${redirectUrl}`"
      target="_self"
    >
      <AuthProviderIcon :icon="icon" />
      <div v-if="!small">{{ $t('loginButton.continueWith') }} {{ name }}</div>
    </a>
  </div>
</template>

<script>
import AuthProviderIcon from '@baserow_enterprise/components/AuthProviderIcon.vue'

export default {
  name: 'OAuth2LoginButton',
  components: { AuthProviderIcon },
  props: {
    redirectUrl: {
      type: String,
      required: true,
    },
    name: {
      type: String,
      required: true,
    },
    icon: {
      type: String,
      required: true,
    },
    small: {
      type: Boolean,
      default: false,
      required: false,
    },
  },
}
</script>
