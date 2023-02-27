<template>
  <div v-if="!redirecting" class="placeholder">
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
    <p v-else class="placeholder__content">{{ content }}</p>
    <div v-if="showBackButton" class="placeholder__action">
      <button
        v-if="isAuthenticated && currentRouteName === 'dashboard'"
        class="button button--large"
        @click="refresh"
      >
        <i class="fas fa-redo-alt"></i>
        {{ $t('errorLayout.refresh') }}
      </button>
      <nuxt-link
        v-else-if="isAuthenticated && currentRouteName !== 'dashboard'"
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
import { logoutAndRedirectToLogin } from '@baserow/modules/core/utils/auth'

export default {
  props: {
    error: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      redirecting: false,
    }
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
    content() {
      return this.error.content || this.$t('errorLayout.error')
    },
    showBackButton() {
      return !this.error.hideBackButton
    },
    currentRouteName() {
      return this.$route.name
    },
    ...mapGetters({
      isAuthenticated: 'auth/isAuthenticated',
    }),
  },
  created() {
    const showSessionExpiredNotification =
      this.$store.getters['auth/isUserSessionExpired']
    if (showSessionExpiredNotification) {
      this.redirecting = true
      logoutAndRedirectToLogin(
        this.$router,
        this.$store,
        showSessionExpiredNotification
      )
    }
  },
  methods: {
    refresh() {
      location.reload()
    },
  },
}
</script>
