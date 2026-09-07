<template>
  <FormGroup
    :error="hasError"
    class="ab-form-group"
    :class="{
      'ab-form-group--horizontal': horizontal,
      'ab-form-group--horizontal-variable': horizontalVariable,
      'ab-form-group--with-label': label,
      'ab-form-group--error': hasError,
    }"
  >
    <label
      v-if="label"
      class="ab-form-group__label"
      :class="{ 'ab-form-group__label--small': smallLabel }"
    >
      {{ label }}
      <span v-if="required" :title="$t('error.requiredField')">*</span>
    </label>
    <div class="ab-form-group__children">
      <slot />
      <div v-if="hasError" class="ab-form-group__error-message">
        <i class="iconoir-warning-triangle"></i>
        {{ errorMessage }}
      </div>
    </div>
  </FormGroup>
</template>

<script>
export default {
  name: 'ABFormGroup',
  props: {
    errorMessage: {
      type: String,
      required: false,
      default: null,
    },
    label: {
      type: String,
      required: false,
      default: null,
    },
    smallLabel: {
      type: Boolean,
      required: false,
      default: false,
    },
    horizontal: {
      type: Boolean,
      required: false,
      default: false,
    },
    horizontalVariable: {
      type: Boolean,
      required: false,
      default: false,
    },
    required: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  computed: {
    hasError() {
      return Boolean(this.errorMessage)
    },
  },
}
</script>
