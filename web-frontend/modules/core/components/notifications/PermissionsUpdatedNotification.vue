<template>
  <Alert
    close-button
    shadow
    simple
    type="warning"
    icon="exclamation"
    :title="$t('permissionsUpdatedNotification.title')"
    @close="close"
    >{{ $t('permissionsUpdatedNotification.content') }}
    <a
      class="button margin-top-1"
      :class="{ 'button--loading': loading }"
      @click="reload()"
      >{{ $t('permissionsUpdatedNotification.action') }}
    </a>
  </Alert>
</template>

<script>
export default {
  name: 'PermissionsUpdatedNotification',
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
      this.$store.dispatch('notification/setPermissionsUpdated', false)
    },
  },
}
</script>
