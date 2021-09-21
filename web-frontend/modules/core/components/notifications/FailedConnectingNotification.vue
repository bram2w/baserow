<template>
  <div
    class="alert alert--simple alert--with-shadow alert--has-icon alert--error"
  >
    <div class="alert__icon">
      <i class="fas fa-exclamation"></i>
    </div>
    <div class="alert__title">
      {{ $t('failedConnectingNotification.title') }}
    </div>
    <p class="alert__content">
      {{ $t('failedConnectingNotification.content') }}
    </p>
    <a
      class="button margin-top-1"
      :class="{ 'button--loading': loading }"
      @click="reload()"
      >{{ $t('failedConnectingNotification.action') }}</a
    >
  </div>
</template>

<script>
export default {
  name: 'FailedConnectingNotification',
  data() {
    return {
      loading: false,
    }
  },
  methods: {
    reload() {
      this.loading = true
      location.reload()
    },
  },
}
</script>

<i18n>
{
  "en": {
    "failedConnectingNotification": {
      "title": "Failed",
      "content": "Connection to the server has failed. Please refresh the page.",
      "action": "Refresh page"
    }
  },
  "fr": {
    "failedConnectingNotification": {
      "title": "Échec de connexion",
      "content": "La connexion avec le serveur a été interrompue. Merci de rafraîchir la page.",
      "action": "Rafraîchir la page"
    }
  }
}
</i18n>
