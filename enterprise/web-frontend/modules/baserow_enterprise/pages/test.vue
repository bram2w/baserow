<template>
  <h2>Enterprise plugin is loaded: {{ loaded }}</h2>
</template>

<script>
export default {
  layout: 'app',
  data() {
    return {
      loaded: false,
    }
  },
  mounted() {
    this.loaded = true
  },
}
</script>
