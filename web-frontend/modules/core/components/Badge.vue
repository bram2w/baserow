<template>
  <div
    class="badge"
    :class="{
      'badge--primary': primary,
      'badge--success': success,
      'badge-warning': warning,
      'badge--error': error,
    }"
  >
    <slot />
  </div>
</template>

<script>
export default {
  name: 'Badge',
  props: {
    primary: {
      type: Boolean,
      required: false,
      default: false,
    },
    success: {
      type: Boolean,
      required: false,
      default: false,
    },
    warning: {
      type: Boolean,
      required: false,
      default: false,
    },
    error: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
}
</script>
