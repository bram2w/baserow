<template>
  <Alert loading simple shadow :title="$t('pastingNotification.title')">
    {{ $t('pastingNotification.content') }}
  </Alert>
</template>

<script>
export default {
  name: 'PastingNotification',
}
</script>
