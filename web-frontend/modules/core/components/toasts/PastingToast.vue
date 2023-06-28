<template>
  <Alert loading simple shadow :title="$t('PastingToast.title')">
    {{ $t('PastingToast.content') }}
  </Alert>
</template>

<script>
export default {
  name: 'PastingToast',
}
</script>
