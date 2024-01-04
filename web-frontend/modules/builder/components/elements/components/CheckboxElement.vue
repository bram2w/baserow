<template>
  <div class="checkbox-element">
    <input
      class="checkbox-element__input"
      type="checkbox"
      :checked="value"
      :required="element.required"
      :disabled="isEditMode"
      @change="toggleValue"
    />
    <label
      v-if="resolvedLabel"
      class="checkbox-element__label"
      @click="toggleValue"
    >
      {{ resolvedLabel }}
    </label>
  </div>
</template>

<script>
import formElement from '@baserow/modules/builder/mixins/formElement'
import { ensureBoolean } from '@baserow/modules/core/utils/validator'

export default {
  name: 'CheckboxElement',
  mixins: [formElement],
  data() {
    return {
      value: false,
    }
  },
  computed: {
    defaultValueResolved() {
      try {
        return ensureBoolean(this.resolveFormula(this.element.default_value))
      } catch {
        return false
      }
    },
    resolvedLabel() {
      return this.resolveFormula(this.element.label)
    },
  },
  watch: {
    defaultValueResolved: {
      handler(value) {
        this.value = value
      },
      immediate: true,
    },
    value(value) {
      this.setFormData(value)
    },
  },
  methods: {
    toggleValue() {
      if (!this.isEditMode) {
        this.value = !this.value
      }
    },
  },
}
</script>
