<template>
  <FormElement class="control" :class="{ 'control--horizontal': horizontal }">
    <label
      v-if="label"
      class="control__label"
      :class="{ 'control__label--small': smallLabel }"
    >
      {{ label }}
    </label>
    <div class="control__elements">
      <textarea
        :value="value"
        :rows="nbRows"
        :placeholder="placeholder"
        class="input paragraph-element-form__value"
        :class="{
          'input--error': hasError,
        }"
        @input="$emit('input', $event.target.value)"
        @keydown.enter.stop
        @blur="$emit('blur', $event)"
      />
    </div>
    <div v-if="hasError" class="error">
      {{ error }}
    </div>
  </FormElement>
</template>

<script>
export default {
  props: {
    value: {
      type: String,
      required: true,
    },
    label: {
      type: String,
      required: false,
      default: '',
    },
    placeholder: {
      type: String,
      required: false,
      default: '',
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
    error: {
      type: String,
      required: false,
      default: '',
    },
  },
  computed: {
    hasError() {
      return Boolean(this.error)
    },
    nbRows() {
      return this.value.split(/\n/).length > 1 ? 12 : 1
    },
  },
}
</script>
