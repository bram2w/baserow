<template>
  <div>
    <Notifications></Notifications>
    <div class="auth__page">
      <nuxt />
    </div>
  </div>
</template>

<script>
import Notifications from '@baserow/modules/core/components/notifications/Notifications'

export default {
  components: { Notifications },
  middleware: ['settings', 'urlCheck'],
  head() {
    return {
      bodyAttrs: {
        class: 'auth__body',
      },
    }
  },
}
</script>
