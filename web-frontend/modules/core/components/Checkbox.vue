<template>
  <div class="checkbox" :class="{ active: value }" @click="toggle(value)">
    <slot></slot>
  </div>
</template>

<script>
export default {
  name: 'Checkbox',
  props: {
    value: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  methods: {
    toggle(value) {
      this.$emit('input', !value)
    },
  },
}
</script>
