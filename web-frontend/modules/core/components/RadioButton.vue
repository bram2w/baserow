<template>
  <Button
    type="secondary"
    v-bind="restProps"
    :loading="loading"
    :disabled="disabled"
    :icon="icon"
    :title="title"
    :active="selected"
    @click.prevent="select(value)"
  >
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
    loading: {
      type: Boolean,
      required: false,
      default: false,
    },
    disabled: {
      type: Boolean,
      required: false,
      default: false,
    },
    icon: {
      type: String,
      required: false,
      default: '',
    },
    title: {
      type: String,
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
