<template>
  <div class="radio" :class="classNames" @click="select(value)">
    <div v-if="loading" class="radio__loading"></div>
    <div v-else class="radio__input">
      <input
        type="radio"
        :value="value"
        :checked="modelValue === value"
        :disabled="disabled || loading"
      />
      <label></label>
    </div>
    <div v-if="hasSlot" class="radio__label">
      <slot></slot>
    </div>
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
      default: '',
    },
    modelValue: {
      type: [String, Number, Boolean, Object],
      required: false,
      default: '',
    },
    disabled: {
      type: Boolean,
      required: false,
      default: false,
    },
    loading: {
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
        'radio--loading': this.loading,
        selected: this.modelValue === this.value,
      }
    },
    selected() {
      return this.modelValue === this.value
    },
    hasSlot() {
      return !!this.$slots.default
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
