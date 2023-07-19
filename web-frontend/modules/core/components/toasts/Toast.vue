<template>
  <Alert
    simple
    shadow
    close-button
    icon="exclamation"
    :type="toast.type"
    :title="toast.title"
    @close="close(toast)"
  >
    {{ toast.message }}
  </Alert>
</template>

<script>
export default {
  name: 'Toast',
  props: {
    toast: {
      type: Object,
      required: true,
    },
  },
  mounted() {
    setTimeout(() => {
      this.close(this.toast)
    }, 5000)
  },
  methods: {
    close(toast) {
      this.$store.dispatch('toast/remove', toast)
    },
  },
}
</script>
