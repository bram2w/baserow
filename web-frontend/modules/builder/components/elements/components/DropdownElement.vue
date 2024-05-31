<template>
  <div class="control">
    <label v-if="element.label" class="control__label">
      {{ labelResolved }}
      <span
        v-if="element.label && element.required"
        :title="$t('error.requiredField')"
        >*</span
      >
    </label>
    <ABDropdown
      v-model="inputValue"
      class="dropdown-element"
      :class="{
        'dropdown-element--error': displayFormDataError,
      }"
      :placeholder="placeholderResolved"
      :show-search="false"
      :multiple="element.multiple"
      @hide="onFormElementTouch"
    >
      <DropdownItem
        v-for="option in element.options"
        :key="option.id"
        :name="option.name || option.value"
        :value="option.value"
      ></DropdownItem>
    </ABDropdown>
    <div v-if="displayFormDataError" class="error">
      <i class="iconoir-warning-triangle"></i>
      {{ $t('error.requiredField') }}
    </div>
  </div>
</template>

<script>
import formElement from '@baserow/modules/builder/mixins/formElement'
import {
  ensureString,
  ensureArray,
} from '@baserow/modules/core/utils/validator'

export default {
  name: 'DropdownElement',
  mixins: [formElement],
  props: {
    /**
     * @type {Object}
     * @property {string} label - The label displayed above the dropdown
     * @property {string} default_value - The default value selected
     * @property {string} placeholder - The placeholder value of the dropdown
     * @property {boolean} required - If the element is required for form submission
     * @property {boolean} multiple - If the dropdown allows multiple selections
     * @property {Array} options - The options of the dropdown
     */
    element: {
      type: Object,
      required: true,
    },
  },
  computed: {
    labelResolved() {
      return ensureString(this.resolveFormula(this.element.label))
    },
    placeholderResolved() {
      return ensureString(this.resolveFormula(this.element.placeholder))
    },
    defaultValueResolved() {
      if (this.element.multiple) {
        return ensureArray(
          this.resolveFormula(this.element.default_value)
        ).reduce((acc, value) => {
          if (
            !acc.includes(value) &&
            this.element.options.some((o) => o.value === value)
          ) {
            acc.push(value)
          }
          return acc
        }, [])
      } else {
        // Always return a string if we have a default value, otherwise
        // set the value to null as single select fields will only skip
        // field preparation if the value is null.
        const resolvedSingleValue = ensureString(
          this.resolveFormula(this.element.default_value)
        )
        return resolvedSingleValue.length ? resolvedSingleValue : null
      }
    },
  },
  watch: {
    defaultValueResolved: {
      handler(newValue) {
        this.inputValue = newValue
      },
      immediate: true,
    },
    'element.multiple'() {
      this.setFormData(this.defaultValueResolved)
    },
  },
}
</script>
