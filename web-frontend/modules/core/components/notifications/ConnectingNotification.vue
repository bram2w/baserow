<template>
  <Alert loading shadow simple :title="$t('connectingNotification.title')"
    >{{ $t('connectingNotification.content') }}
  </Alert>
</template>

<script>
export default {
  name: 'ConnectingNotification',
}
</script>
