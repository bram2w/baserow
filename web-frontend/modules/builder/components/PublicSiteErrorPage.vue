<template>
  <div v-if="!redirecting" class="placeholder">
    <div class="placeholder__logo">
      <nuxt-link
        :to="{
          name: 'application-builder-page',
          params: { pathMatch: '/' },
        }"
      >
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
    <div class="placeholder__action">
      <button class="button button--large" @click="$router.go(-1)">
        <i class="fas fa-arrow-left"></i>
        {{ $t('action.back') }}
      </button>
    </div>
  </div>
</template>

<script>
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
  },
}
</script>
