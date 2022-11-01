<template>
  <div>
    <a
      class="auth-provider-buttons__button"
      :href="`${redirectUrl}`"
      target="_self"
    >
      <AuthProviderIcon :icon="icon" />{{ $t('loginButton.continueWith') }}
      {{ name }}
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
  },
}
</script>
