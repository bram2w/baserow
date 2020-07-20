<template>
  <div v-if="error.visible" class="alert alert--error alert--has-icon">
    <div class="alert__icon">
      <i class="fas fa-exclamation"></i>
    </div>
    <div class="alert__title">{{ error.title }}</div>
    <p class="alert__content">{{ error.message }}</p>
  </div>
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
