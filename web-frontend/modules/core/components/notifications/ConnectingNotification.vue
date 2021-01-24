<template>
  <div class="alert alert--simple alert--with-shadow alert--has-icon">
    <div class="alert__icon">
      <div class="loading alert__icon-loading"></div>
    </div>
    <div class="alert__title">Reconnecting</div>
    <p class="alert__content">Reconnecting with server.</p>
  </div>
</template>

<script>
export default {
  name: 'ConnectingNotification',
}
</script>
