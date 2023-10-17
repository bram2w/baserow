<template>
  <Alert loading shadow simple :title="$t('connectingToast.title')"
    ><p>{{ $t('connectingToast.content') }}</p>
  </Alert>
</template>

<script>
export default {
  name: 'ConnectingToast',
}
</script>
