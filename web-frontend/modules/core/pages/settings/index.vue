<template>
  <div>
    <!-- This is where we will implement tabs to go to another settings page -->
    <NuxtChild :group="group" />
  </div>
</template>

<script>
export default {
  name: 'Settings',
  layout: 'app',
  computed: {
    group() {
      return this.$store.getters['group/get'](
        parseInt(this.$route.params.groupId, 10)
      )
    },
  },
}
</script>
