<template>
  <Alert loading simple shadow :title="$t('clearingToast.title')">
    {{ $t('clearingToast.content') }}
  </Alert>
</template>

<script>
export default {
  name: 'ClearingToast',
}
</script>
