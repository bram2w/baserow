<template>
  <input
    v-model="inputValue"
    class="preview-navigation-bar-input"
    :class="{
      'preview-navigation-bar-input--invalid': invalidValueForType,
    }"
  />
</template>

<script>
export default {
  props: {
    defaultValue: {
      type: [String, Number],
      required: false,
      default: '',
    },
    validationFn: {
      type: Function,
      required: true,
    },
  },
  data() {
    return {
      value: this.defaultValue,
      invalidValueForType: false,
    }
  },
  computed: {
    inputValue: {
      get() {
        return this.value
      },
      set(inputValue) {
        this.invalidValueForType = false
        this.value = inputValue
        try {
          this.$emit('change', this.validationFn(this.value))
        } catch (error) {
          this.invalidValueForType = true
        }
      },
    },
  },
  watch: {
    defaultValue(newValue) {
      this.inputValue = newValue
    },
  },
}
</script>
