<template>
  <Alert loading simple shadow :title="$t('copyingToast.title')">
    <p>{{ $t('copyingToast.content') }}</p>
  </Alert>
</template>

<script>
export default {
  name: 'CopyingToast',
}
</script>
