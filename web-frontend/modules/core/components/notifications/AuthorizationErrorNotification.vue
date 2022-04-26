<template>
  <div
    class="alert alert--simple alert--with-shadow alert--has-icon alert--error"
  >
    <div class="alert__icon">
      <i class="fas fa-exclamation"></i>
    </div>
    <div class="alert__title">
      {{ $t('AuthorizationErrorNotification.title') }}
    </div>
    <p class="alert__content">
      {{ $t('AuthorizationErrorNotification.content') }}
    </p>
    <a
      class="button margin-top-1"
      :class="{ 'button--loading': loading }"
      @click="reload()"
      >{{ $t('AuthorizationErrorNotification.action') }}</a
    >
  </div>
</template>

<script>
export default {
  name: 'AuthorizationErrorNotification',
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
