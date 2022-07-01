<template>
  <div>
    <Notifications></Notifications>
    <div class="box-page__header"></div>
    <div class="box-page">
      <div class="box">
        <nuxt />
      </div>
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
