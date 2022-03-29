<template>
  <div :data-form-error="error">
    <slot></slot>
  </div>
</template>

<script>
export default {
  name: 'FormElement',
  props: {
    error: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
}
</script>
