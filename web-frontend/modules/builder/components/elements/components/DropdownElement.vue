<template>
  <div class="control">
    <label v-if="element.label" class="control__label">
      {{ labelResolved }}
    </label>
    <Dropdown
      v-model="itemSelected"
      class="dropdown-element"
      :placeholder="placeholderResolved"
      :show-search="false"
    >
      <DropdownItem
        v-for="option in element.options"
        :key="option.id"
        :name="option.name || option.value"
        :value="option.value"
      ></DropdownItem>
    </Dropdown>
  </div>
</template>

<script>
import formElement from '@baserow/modules/builder/mixins/formElement'

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
  data() {
    return {
      itemSelected: null,
    }
  },
  computed: {
    labelResolved() {
      return this.resolveFormula(this.element.label)
    },
    placeholderResolved() {
      return this.resolveFormula(this.element.placeholder).toString()
    },
    defaultValueResolved() {
      // We need to make sure this is always a string since the options aren't formulas
      // and therefore can only be strings. In order to match the default value to
      // an option the default value therefore must be a string as well.
      // true has to match "true" essentially.
      return this.resolveFormula(this.element.default_value).toString()
    },
  },
  watch: {
    itemSelected(value) {
      this.setFormData(value)
    },
    defaultValueResolved: {
      handler(value) {
        this.itemSelected = value
      },
      immediate: true,
    },
  },
}
</script>
