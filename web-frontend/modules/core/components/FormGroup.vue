<template>
  <FormElement
    :error="hasError"
    class="control"
    :class="{
      'control--horizontal': horizontal,
      'control--horizontal-variable': horizontalVariable,
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
      <slot />
      <div v-if="hasError" class="error">
        {{ error }}
      </div>
    </div>
  </FormElement>
</template>

<script>
export default {
  name: 'FormGroup',
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
  },
  computed: {
    hasError() {
      return Boolean(this.error)
    },
  },
}
</script>
