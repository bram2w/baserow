<template>
  <Alert
    simple
    shadow
    type="error"
    icon="iconoir-warning-triangle"
    :title="$t('authorizationErrorToast.title')"
  >
    {{ $t('authorizationErrorToast.content') }}
    <a
      class="button margin-top-1"
      :class="{ 'button--loading': loading }"
      @click="reload()"
      >{{ $t('authorizationErrorToast.action') }}</a
    >
  </Alert>
</template>

<script>
export default {
  name: 'AuthorizationErrorToast',
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
