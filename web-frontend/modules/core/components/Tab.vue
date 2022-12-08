<template lang="html">
  <div v-show="isActive">
    <slot></slot>
  </div>
</template>

<script>
export default {
  name: 'Tab',
  props: {
    title: {
      type: String,
      default: 'Tab',
    },
    disabled: {
      type: Boolean,
      default: () => false,
    },
  },
  data() {
    return {
      isActive: false,
    }
  },
}
</script>
