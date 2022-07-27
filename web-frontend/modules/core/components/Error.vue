<template>
  <Alert
    v-if="error.visible"
    type="error"
    icon="exclamation"
    :title="error.title"
    >{{ error.message }}</Alert
  >
</template>

<script>
/**
 * This component works the best if the parent has the error mixin.
 */
export default {
  props: {
    error: {
      required: true,
      type: Object,
    },
  },
}
</script>
