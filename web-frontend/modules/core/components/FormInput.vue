<template>
  <FormElement
    :error="hasError"
    class="control"
    :class="{
      'control--horizontal': horizontal,
    }"
  >
    <label
      v-if="label"
      class="control__label"
      :class="{ 'control__label--small': smallLabel }"
    >
      {{ label }}
    </label>
    <div class="control__elements">
      <div
        :class="{
          'form-input': true,
          'form-input--with-icon': hasIcon,
          'form-input--with-icon-left': iconLeft,
          'form-input--with-icon-right': iconRight,
          'form-input--error': hasError,
          'form-input--large': large,
          'form-input--monospace': monospace,
          'form-input--loading': loading,
          'form-input--disabled': disabled,
        }"
      >
        <input
          ref="base_url"
          class="form-input__input"
          :value="fromValue(value)"
          :disabled="disabled"
          :type="type"
          :placeholder="placeholder"
          @blur="$emit('blur', $event)"
          @input="$emit('input', toValue($event.target.value))"
        />

        <i
          v-if="hasIcon"
          class="form-input__icon fas"
          :class="[`fa-${icon}`]"
        />
      </div>
      <div v-if="hasError" class="error">
        {{ error }}
      </div>
    </div>
  </FormElement>
</template>

<script>
export default {
  name: 'FormInput',
  props: {
    error: {
      type: String,
      required: false,
      default: null,
    },
    label: {
      type: String,
      required: false,
      default: null,
    },
    placeholder: {
      type: String,
      required: false,
      default: null,
    },
    value: {
      required: true,
      validator: (value) => true,
    },
    toValue: {
      type: Function,
      required: false,
      default: (value) => value,
    },
    fromValue: {
      type: Function,
      required: false,
      default: (value) => value,
    },
    type: {
      type: String,
      required: false,
      default: 'text',
    },
    disabled: {
      type: Boolean,
      required: false,
      default: false,
    },
    monospace: {
      type: Boolean,
      required: false,
      default: false,
    },
    smallLabel: {
      type: Boolean,
      required: false,
      default: false,
    },
    large: {
      type: Boolean,
      required: false,
      default: false,
    },
    horizontal: {
      type: Boolean,
      required: false,
      default: false,
    },
    loading: {
      type: Boolean,
      required: false,
      default: false,
    },
    iconLeft: {
      type: String,
      required: false,
      default: null,
    },
    iconRight: {
      type: String,
      required: false,
      default: null,
    },
  },
  computed: {
    hasError() {
      return Boolean(this.error)
    },
    hasIcon() {
      return Boolean(this.iconLeft || this.iconRight)
    },
    icon() {
      return this.iconRight || this.iconLeft
    },
  },
}
</script>
