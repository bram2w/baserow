<template>
  <div class="alert alert--simple alert--with-shadow alert--has-icon">
    <div class="alert__icon">
      <div class="loading alert__icon-loading"></div>
    </div>
    <div class="alert__title">{{ $t('connectingNotification.title') }}</div>
    <p class="alert__content">{{ $t('connectingNotification.content') }}</p>
  </div>
</template>

<script>
export default {
  name: 'ConnectingNotification',
}
</script>
