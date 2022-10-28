<template>
  <div>
    <Notifications></Notifications>
    <div class="box-page">
      <nuxt />
    </div>
  </div>
</template>

<script>
import Notifications from '@baserow/modules/core/components/notifications/Notifications'

export default {
  components: { Notifications },
  middleware: ['settings', 'urlCheck'],
}
</script>
