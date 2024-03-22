<template>
  <div @click="toggle">
    <input
      type="checkbox"
      :checked="value"
      :required="required"
      :disabled="disabled"
      class="ab-checkbox__input"
      :class="{
        'ab-checkbox--error': error,
      }"
    />
    <label v-if="hasSlot" class="ab-checkbox__label">
      <slot></slot>
    </label>
  </div>
</template>

<script>
export default {
  name: 'ABCheckbox',
  props: {
    /**
     * The state of the checkbox.
     */
    value: {
      type: Boolean,
      required: false,
      default: false,
    },
    /**
     * Whether the checkbox is disabled.
     */
    disabled: {
      type: Boolean,
      required: false,
      default: false,
    },
    /**
     * Whether the checkbox is required.
     */
    required: {
      type: Boolean,
      required: false,
      default: false,
    },
    /**
     * Whether the checkbox is in error state.
     */
    error: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  computed: {
    hasSlot() {
      return !!this.$slots.default
    },
  },
  methods: {
    toggle() {
      if (this.disabled) return
      this.$emit('input', !this.value)
    },
  },
}
</script>
