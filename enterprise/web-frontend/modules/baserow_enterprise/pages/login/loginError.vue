<template>
  <div>
    <div class="box__head-logo">
      <nuxt-link :to="{ name: 'index' }">
        <img src="@baserow/modules/core/static/img/logo.svg" alt="" />
      </nuxt-link>
    </div>
    <div class="login-box__head">
      <h1 class="box__head-title">
        {{ $t('loginError.title') }}
      </h1>
    </div>
    <p>
      {{ errorMessage }}
    </p>
  </div>
</template>

<script>
export default {
  layout: 'login',
  asyncData({ route, i18n }) {
    const { error } = route.query
    const errorMessageI18nKey = `loginError.${error}`
    let errorMessage = i18n.t('loginError.defaultErrorMessage')
    if (i18n.te(errorMessageI18nKey)) {
      errorMessage = i18n.t(`loginError.${error}`)
    }
    return {
      errorMessage,
    }
  },
  head() {
    return {
      title: this.$t('loginError.title'),
    }
  },
}
</script>
