<template>
  <div :class="readOnly ? 'read-only-form' : ''">
    <slot></slot>
  </div>
</template>

<script>
export default {
  name: 'ReadOnlyForm',
  props: {
    readOnly: {
      required: true,
      type: Boolean,
    },
  },
}
</script>
