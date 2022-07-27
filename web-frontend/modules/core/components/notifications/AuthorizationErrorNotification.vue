<template>
  <Alert
    simple
    shadow
    type="error"
    icon="exclamation"
    :title="$t('AuthorizationErrorNotification.title')"
  >
    {{ $t('AuthorizationErrorNotification.content') }}
    <a
      class="button margin-top-1"
      :class="{ 'button--loading': loading }"
      @click="reload()"
      >{{ $t('AuthorizationErrorNotification.action') }}</a
    >
  </Alert>
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
