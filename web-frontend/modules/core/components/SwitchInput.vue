<template>
  <div class="switch" :class="classNames" @click="toggle(value)">
    <slot></slot>
  </div>
</template>

<script>
export default {
  name: 'SwitchInput',
  props: {
    value: {
      type: [Boolean, Number],
      required: false,
      default: false,
    },
    large: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  computed: {
    classNames() {
      return {
        'switch--has-content': Object.prototype.hasOwnProperty.call(
          this.$slots,
          'default'
        ),
        'switch--large': this.large,
        active: this.value === true,
        unknown: this.value !== true && this.value !== false,
      }
    },
  },
  methods: {
    toggle(value) {
      this.$emit('input', !value)
    },
  },
}
</script>
