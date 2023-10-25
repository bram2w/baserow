<template>
  <Alert loading simple shadow :title="$t('PastingToast.title')">
    <p>{{ $t('PastingToast.content') }}</p>
  </Alert>
</template>

<script>
export default {
  name: 'PastingToast',
}
</script>
