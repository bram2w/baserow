<template>
  <Alert
    close-button
    shadow
    simple
    type="warning"
    icon="exclamation"
    :title="$t('permissionsUpdatedToast.title')"
    @close="close"
    >{{ $t('permissionsUpdatedToast.content') }}
    <a
      class="button margin-top-1"
      :class="{ 'button--loading': loading }"
      @click="reload()"
      >{{ $t('permissionsUpdatedToast.action') }}
    </a>
  </Alert>
</template>

<script>
export default {
  name: 'PermissionsUpdatedToast',
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
    close() {
      this.$store.dispatch('toast/setPermissionsUpdated', false)
    },
  },
}
</script>
