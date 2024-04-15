<template>
  <div class="radio-button">
    <ButtonIcon
      v-if="type === 'icon'"
      type="primary"
      v-bind="restProps"
      @click.prevent="select(value)"
    >
    </ButtonIcon>

    <Chips
      v-if="type === 'chips'"
      type="primary"
      v-bind="restProps"
      @click.prevent="select(value)"
    >
      <slot></slot>
    </Chips>
  </div>
</template>

<script>
export default {
  name: 'RadioButton',
  model: {
    prop: 'modelValue',
    event: 'input',
  },
  props: {
    type: {
      type: String,
      required: false,
      validator: function (value) {
        return ['icon', 'chips'].includes(value)
      },
      default: 'icon',
    },
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
