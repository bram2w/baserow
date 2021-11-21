<template>
  <div class="radio" :class="classNames" @click="select(value)">
    <slot></slot>
  </div>
</template>

<script>
export default {
  name: 'Radio',
  model: {
    prop: 'modelValue',
    event: 'input',
  },
  props: {
    value: {
      type: [String, Number, Boolean, Object],
      required: false,
    },
    modelValue: {
      type: [String, Number, Boolean, Object],
      required: false,
    },
    disabled: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  computed: {
    classNames() {
      return {
        'radio--has-content': Object.prototype.hasOwnProperty.call(
          this.$slots,
          'default'
        ),
        'radio--disabled': this.disabled,
        selected: this.modelValue === this.value,
      }
    },
  },
  methods: {
    select(value) {
      if (this.disabled) {
        return
      }
      this.$emit('input', value)
    },
  },
}
</script>
