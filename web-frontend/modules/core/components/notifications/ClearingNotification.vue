<template>
  <Alert loading simple shadow :title="$t('clearingNotification.title')">
    {{ $t('clearingNotification.content') }}
  </Alert>
</template>

<script>
export default {
  name: 'ClearingNotification',
}
</script>
