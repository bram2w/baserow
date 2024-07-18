<template>
  <ABFormGroup
    :error-message="displayFormDataError ? $t('error.requiredField') : ''"
    :style="getStyleOverride('input')"
  >
    <ABCheckbox
      v-model="inputValue"
      :required="element.required"
      :read-only="isEditMode"
    >
      {{ resolvedLabel }}
      <span
        v-if="element.label && element.required"
        :title="$t('error.requiredField')"
        >*</span
      >
    </ABCheckbox>
  </ABFormGroup>
</template>

<script>
import formElement from '@baserow/modules/builder/mixins/formElement'
import {
  ensureBoolean,
  ensureString,
} from '@baserow/modules/core/utils/validator'

export default {
  name: 'CheckboxElement',
  mixins: [formElement],
  computed: {
    defaultValueResolved() {
      try {
        return ensureBoolean(this.resolveFormula(this.element.default_value))
      } catch {
        return false
      }
    },
    resolvedLabel() {
      return ensureString(this.resolveFormula(this.element.label))
    },
  },
  watch: {
    defaultValueResolved: {
      handler(newValue) {
        this.inputValue = newValue
      },
      immediate: true,
    },
  },
}
</script>
