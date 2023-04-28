<template>
  <div v-if="isActive" class="tab">
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
    tooltip: {
      type: String,
      default: null,
      required: false,
    },
    to: {
      type: Object,
      default: () => {},
      required: false,
    },
  },
  data() {
    return {
      isActive: false,
    }
  },
}
</script>
