<template>
  <div class="checkbox" :class="classNames" @click="toggle(value)">
    <i v-if="value === true" class="checkbox__checked-icon iconoir-check"></i>
    <label class="checkbox__label"><slot></slot></label>
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
    disabled: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  computed: {
    classNames() {
      return {
        'checkbox--has-content': Object.prototype.hasOwnProperty.call(
          this.$slots,
          'default'
        ),
        'checkbox--disabled': this.disabled,
        active: this.value === true,
      }
    },
  },
  methods: {
    toggle(value) {
      if (this.disabled) {
        return
      }
      this.$emit('input', !value)
    },
  },
}
</script>
