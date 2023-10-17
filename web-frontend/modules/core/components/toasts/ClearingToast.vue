<template>
  <Alert loading simple shadow :title="$t('clearingToast.title')">
    <p>{{ $t('clearingToast.content') }}</p>
  </Alert>
</template>

<script>
export default {
  name: 'ClearingToast',
}
</script>
