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
      The page you are looking for has not been found. This might be because URL
      is incorrect or that you don’t have permission to view this page.
    </p>
    <p v-else class="placeholder__content">
      Something went wrong while loading the page. Our developers have been
      notified of the issue. Please try to refresh or return to the dashboard.
    </p>
    <div class="placeholder__action">
      <nuxt-link
        v-if="isAuthenticated"
        :to="{ name: 'dashboard' }"
        class="button button--large"
      >
        <i class="fas fa-arrow-left"></i>
        Back to dashboard
      </nuxt-link>
      <nuxt-link v-else :to="{ name: 'login' }" class="button button--large">
        <i class="fas fa-arrow-left"></i>
        Back to login
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
      return this.error.message || 'Something went wrong'
    },
    ...mapGetters({
      isAuthenticated: 'auth/isAuthenticated',
    }),
  },
}
</script>
