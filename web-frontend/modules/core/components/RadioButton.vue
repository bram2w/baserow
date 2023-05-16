<template>
  <Button color="light" v-bind="restProps" @click.prevent="select(value)">
    <slot></slot>
  </Button>
</template>

<script>
export default {
  name: 'RadioButton',
  model: {
    prop: 'modelValue',
    event: 'input',
  },
  props: {
    value: {
      type: [String, Number, Boolean, Object],
      required: false,
      default: '',
    },
    modelValue: {
      type: [String, Number, Boolean, Object],
      required: false,
      default: '',
    },
  },
  computed: {
    selected() {
      return this.modelValue === this.value
    },
    restProps() {
      const { value, modelValue, ...rest } = this.$attrs
      if (this.selected) {
        rest.active = true
      }
      return rest
    },
  },
  methods: {
    select(value) {
      if (this.disabled || this.selected) {
        return
      }
      this.$emit('input', value)
    },
  },
}
</script>
