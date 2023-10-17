<template>
  <Alert
    v-if="error.visible"
    type="error"
    icon="iconoir-warning-triangle"
    :title="error.title"
    ><p>{{ error.message }}</p></Alert
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
