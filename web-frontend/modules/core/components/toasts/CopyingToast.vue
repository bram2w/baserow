<template>
  <Alert loading simple shadow :title="$t('copyingToast.title')">
    {{ $t('copyingToast.content') }}
  </Alert>
</template>

<script>
export default {
  name: 'CopyingToast',
}
</script>
