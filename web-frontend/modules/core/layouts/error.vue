<template>
  <div class="placeholder">
    <div class="placeholder__logo">
      <nuxt-link :to="{ name: 'index' }">
        <img
          class="placeholder__logo-image"
          src="@baserow/modules/core/static/img/logo.svg"
          alt=""
        />
      </nuxt-link>
    </div>
    <h1 class="placeholder__title">{{ message }}</h1>
    <p v-if="error.statusCode === 404" class="placeholder__content">
      {{ $t('errorLayout.notFound') }}
    </p>
    <p v-else class="placeholder__content">
      {{ $t('errorLayout.error') }}
    </p>
    <div class="placeholder__action">
      <nuxt-link
        v-if="isAuthenticated"
        :to="{ name: 'dashboard' }"
        class="button button--large"
      >
        <i class="fas fa-arrow-left"></i>
        {{ $t('errorLayout.backDashboard') }}
      </nuxt-link>
      <nuxt-link v-else :to="{ name: 'login' }" class="button button--large">
        <i class="fas fa-arrow-left"></i>
        {{ $t('errorLayout.backLogin') }}
      </nuxt-link>
    </div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'

export default {
  props: {
    error: {
      type: Object,
      required: true,
    },
  },
  head() {
    return {
      title: this.message,
    }
  },
  computed: {
    statusCode() {
      return (this.error && this.error.statusCode) || 500
    },
    message() {
      return this.error.message || this.$t('errorLayout.wrong')
    },
    ...mapGetters({
      isAuthenticated: 'auth/isAuthenticated',
    }),
  },
}
</script>
