<template>
  <Alert loading simple shadow :title="$t('copyingNotification.title')">
    {{ $t('copyingNotification.content') }}
  </Alert>
</template>

<script>
export default {
  name: 'CopyingNotification',
}
</script>
