<template>
  <ABFormGroup
    :label="labelResolved"
    :required="element.required"
    :error-message="displayFormDataError ? $t('error.requiredField') : ''"
  >
    <ABDropdown
      v-if="element.show_as_dropdown"
      v-model="inputValue"
      class="choice-element"
      :class="{
        'choice-element--error': displayFormDataError,
      }"
      :placeholder="
        element.options.length
          ? placeholderResolved
          : $t('choiceElement.addOptions')
      "
      :show-search="false"
      :multiple="element.multiple"
      @hide="onFormElementTouch"
    >
      <ABDropdownItem
        v-for="option in element.options"
        :key="option.id"
        :name="option.name || option.value"
        :value="option.value"
      />
    </ABDropdown>
    <template v-else>
      <template v-if="element.options.length">
        <template v-if="element.multiple">
          <ABCheckbox
            v-for="option in optionsBooleanResolved"
            :key="option.id"
            :read-only="isEditMode"
            :error="displayFormDataError"
            :value="option.booleanValue"
            @input="onOptionChange(option, $event)"
          >
            {{ option.name || option.value }}
          </ABCheckbox>
        </template>
        <template v-else>
          <ABRadio
            v-for="option in element.options"
            :key="option.id"
            :read-only="isEditMode"
            :error="displayFormDataError"
            :value="option.value === inputValue"
            @input="onOptionChange(option, $event)"
          >
            {{ option.name || option.value }}
          </ABRadio>
        </template>
      </template>
      <template v-else>{{ $t('choiceElement.addOptions') }}</template>
    </template>
  </ABFormGroup>
</template>

<script>
import formElement from '@baserow/modules/builder/mixins/formElement'
import {
  ensureString,
  ensureArray,
} from '@baserow/modules/core/utils/validator'

export default {
  name: 'ChoiceElement',
  mixins: [formElement],
  props: {
    /**
     * @type {Object}
     * @property {string} label - The label displayed above the choice element
     * @property {string} default_value - The default value selected
     * @property {string} placeholder - The placeholder value of the choice element
     * @property {boolean} required - If the element is required for form submission
     * @property {boolean} multiple - If the choice element allows multiple selections
     * @property {boolean} show_as_dropdown - If the choice element should be displayed as a dropdown
     * @property {Array} options - The options of the choice element
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
    optionsBooleanResolved() {
      return this.element.options.map((option) => ({
        ...option,
        booleanValue: this.inputValue.includes(option.value),
      }))
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
  methods: {
    onOptionChange(option, value) {
      if (value) {
        if (this.element.multiple) {
          this.inputValue = [...this.inputValue, option.value]
        } else {
          this.inputValue = option.value
        }
      } else if (this.element.multiple) {
        this.inputValue = this.inputValue.filter((v) => v !== option.value)
      }
    },
  },
}
</script>
