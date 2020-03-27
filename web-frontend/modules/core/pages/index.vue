<template>
  <div>{{ test }}</div>
</template>

<script>
export default {
  fetch({ store, redirect }) {
    const name = store.getters['auth/isAuthenticated'] ? 'dashboard' : 'login'
    redirect({ name: name })
  }
}
</script>
