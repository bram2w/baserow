<template>
  <Context ref="editContext">
    <div class="formula-field">
      <div class="formula-field__input">
        <AutoExpandableTextarea
          ref="textAreaFormulaInput"
          v-model="formula"
          class="formula-field__input-formula"
          placeholder="Enter your formula here, use tab to autocomplete"
          @blur="$emit('blur', $event)"
          @click="recalcAutoComplete"
          @keyup="recalcAutoComplete"
          @keydown.tab.prevent="doAutoCompleteAfterTab"
          @keydown.enter.exact.prevent="$refs.editContext.hide()"
        ></AutoExpandableTextarea>
      </div>
      <div v-if="error" class="formula-field__input-error">{{ error }}</div>
      <div class="formula-field__body">
        <div class="formula-field__items">
          <FormulaFieldItemGroup
            :filtered-items="filteredFields"
            :unfiltered-items="fields"
            title="Fields"
            @hover-item="selectItem"
            @click-item="doAutoComplete(null, $event)"
          >
          </FormulaFieldItemGroup>
          <FormulaFieldItemGroup
            :filtered-items="filteredFunctions"
            :unfiltered-items="functions"
            title="Functions"
            @hover-item="selectItem"
            @click-item="doAutoComplete($event, null)"
          >
          </FormulaFieldItemGroup>
          <FormulaFieldItemGroup
            :filtered-items="filteredOperators"
            :unfiltered-items="unfilteredOperators"
            title="Operators"
            :show-operator="true"
            @hover-item="selectItem"
            @click-item="doAutoComplete($event, null)"
          >
          </FormulaFieldItemGroup>
        </div>
        <FormulaFieldItemDescription :selected-item="selectedItem">
        </FormulaFieldItemDescription>
      </div>
    </div>
  </Context>
</template>

<script>
import AutoExpandableTextarea from '@baserow/modules/core/components/helpers/AutoExpandableTextarea'
import context from '@baserow/modules/core/mixins/context'

import {
  autocompleteFormula,
  calculateFilteredFunctionsAndFieldsBasedOnCursorLocation,
} from '@baserow/modules/database/formula/autocompleter/formulaAutocompleter'
import FormulaFieldItemGroup from '@baserow/modules/database/components/formula/FormulaFieldItemGroup'
import FormulaFieldItemDescription from '@baserow/modules/database/components/formula/FormulaFieldItemDescription'

const TAB_KEYCODE = 9

export default {
  name: 'FormulaAdvancedEditContext',
  components: {
    AutoExpandableTextarea,
    FormulaFieldItemDescription,
    FormulaFieldItemGroup,
  },
  mixins: [context],
  props: {
    table: {
      type: Object,
      required: true,
    },
    fields: {
      type: Array,
      required: true,
    },
    value: {
      type: String,
      required: true,
    },
    error: {
      type: String,
      required: false,
      default: null,
    },
  },
  data() {
    const functions = this.getAndWrapFunctions()
    return {
      functions,
      selectedItem: functions[0],
      filteredFunctions: functions,
      filteredFields: [],
    }
  },
  computed: {
    formula: {
      get() {
        return this.value
      },
      set(value) {
        this.$emit('input', value)
      },
    },
    fieldItems() {
      return this.fields.map((f) =>
        this.wrapItem(
          f.name,
          this.getFieldIcon(f),
          `A ${f.type} field`,
          `concat(field('${f.name}'), ' extra text ')`,
          `field('${f.name}')`,
          false,
          f
        )
      )
    },
    unfilteredOperators() {
      return this.functions.filter((f) => f.operator)
    },
    filteredOperators() {
      return this.filteredFunctions.filter((f) => f.operator)
    },
  },
  mounted() {
    this.recalcAutoComplete()
  },
  methods: {
    getFieldIcon(field) {
      const fieldType = this.$registry.get('field', field.type)
      return `fa-${fieldType.getIconClass()}`
    },
    funcTypeToIconClass(func) {
      const formulaType = func.getFormulaType()
      return {
        text: 'fa-font',
        char: 'fa-font',
        number: 'fa-hashtag',
        boolean: 'fa-check-square',
        date: 'fa-calendar-alt',
        date_interval: 'fa-history',
        special: 'fa-square-root-alt',
      }[formulaType]
    },
    resetFilters() {
      this.filteredFunctions = this.functions
      this.filteredFields = this.fieldItems
    },
    selectItem(item, resetFilters = true) {
      this.selectedItem.isSelected = false
      this.selectedItem = false
      this.selectedItem = item
      item.isSelected = true
    },
    recalcAutoComplete(event) {
      // Prevent tabs from doing anything as doAutocomplete will handle a tab instead.
      if (event && event.keyCode === TAB_KEYCODE) {
        event.preventDefault()
        return
      }
      const cursorLocation =
        this.$refs.textAreaFormulaInput !== undefined
          ? this.$refs.textAreaFormulaInput.$refs.inputTextArea.selectionStart
          : 0

      const { filteredFields, filteredFunctions, filtered } =
        calculateFilteredFunctionsAndFieldsBasedOnCursorLocation(
          this.formula,
          cursorLocation,
          this.fieldItems,
          this.functions
        )

      this.filteredFunctions = filteredFunctions
      this.filteredFields = filteredFields

      if (filtered) {
        if (this.filteredFunctions.length > 0) {
          this.selectItem(filteredFunctions[0], false)
        } else if (this.filteredFields.length > 0) {
          this.selectItem(filteredFields[0], false)
        }
      }
    },
    doAutoCompleteAfterTab() {
      this.doAutoComplete(this.filteredFunctions[0], this.filteredFields[0])
    },
    doAutoComplete(functionCandidate, fieldCandidate) {
      const startingCursorLocation =
        this.$refs.textAreaFormulaInput.$refs.inputTextArea.selectionStart

      const { autocompletedFormula, newCursorPosition } = autocompleteFormula(
        this.formula,
        startingCursorLocation,
        functionCandidate,
        fieldCandidate
      )
      this.formula = autocompletedFormula

      this.$nextTick(() => {
        this.$refs.textAreaFormulaInput.$refs.inputTextArea.focus()
        this.$refs.textAreaFormulaInput.$refs.inputTextArea.setSelectionRange(
          newCursorPosition,
          newCursorPosition
        )
        this.recalcAutoComplete()
      })
    },
    async openContext(triggeringEl) {
      await this.$refs.editContext.show(
        triggeringEl,
        'top',
        'left',
        -triggeringEl.scrollHeight - 3,
        -1
      )
      this.$nextTick(() => {
        this.$refs.textAreaFormulaInput.$refs.inputTextArea.focus()
        this.$refs.textAreaFormulaInput.$refs.inputTextArea.setSelectionRange(
          triggeringEl.selectionStart,
          triggeringEl.selectionEnd
        )
      })
    },
    wrapItem(value, icon, description, examples, syntaxUsage, operator, item) {
      return {
        value,
        icon,
        isSelected: false,
        description,
        examples,
        syntaxUsage,
        operator,
        item,
      }
    },
    getAndWrapFunctions() {
      return Object.values(this.$registry.getAll('formula_function')).map((f) =>
        this.wrapItem(
          f.getType(),
          this.funcTypeToIconClass(f),
          f.getDescription(),
          f.getExamples(),
          f.getSyntaxUsage(),
          f.getOperator(),
          f
        )
      )
    },
  },
}
</script>
