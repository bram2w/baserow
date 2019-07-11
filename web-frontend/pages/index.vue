<template>
  <div>{{ test }}</div>
</template>

<script>
export default {
  fetch({ store, redirect }) {
    const name = store.getters['auth/isAuthenticated'] ? 'app' : 'login'
    redirect({ name: name })
  }
}
</script>
