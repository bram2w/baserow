<template>
  <div>
    <Notifications></Notifications>
    <div class="box-page-header"></div>
    <div class="box-page">
      <div class="box login-page login-page-login">
        <nuxt />
      </div>
    </div>
  </div>
</template>

<script>
import Notifications from '@baserow/modules/core/components/notifications/Notifications'

export default {
  components: { Notifications },
}
</script>
