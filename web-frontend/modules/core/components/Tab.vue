<template lang="html">
  <div v-show="isActive" class="tabs__item">
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
  },
  data() {
    return {
      isActive: true,
    }
  },
}
</script>
