<template>
  <Alert loading shadow simple :title="$t('connectingToast.title')"
    >{{ $t('connectingToast.content') }}
  </Alert>
</template>

<script>
export default {
  name: 'ConnectingToast',
}
</script>
