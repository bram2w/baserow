<template>
  <div class="control">
    <label v-if="element.label" class="control__label">
      {{ labelResolved }}
      <span
        v-if="element.label && element.required"
        class="control__label--required"
        :title="$t('error.requiredField')"
        >*</span
      >
    </label>
    <Dropdown
      v-model="inputValue"
      class="dropdown-element"
      :class="{
        'dropdown-element--error': displayFormDataError,
      }"
      :placeholder="placeholderResolved"
      :show-search="false"
      @hide="onFormElementTouch"
    >
      <DropdownItem
        v-for="option in element.options"
        :key="option.id"
        :name="option.name || option.value"
        :value="option.value"
      ></DropdownItem>
    </Dropdown>
    <div v-if="displayFormDataError" class="error">
      <i class="iconoir-warning-triangle"></i>
      {{ $t('error.requiredField') }}
    </div>
  </div>
</template>

<script>
import formElement from '@baserow/modules/builder/mixins/formElement'
import { ensureString } from '@baserow/modules/core/utils/validator'

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
      // We need to make sure this is always a string since the options aren't formulas
      // and therefore can only be strings. In order to match the default value to
      // an option the default value therefore must be a string as well.
      // true has to match "true" essentially.
      return ensureString(this.resolveFormula(this.element.default_value))
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
