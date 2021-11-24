<template>
  <div>
    <FieldFormulaInitialSubForm
      :default-values="mergedTypeOptions"
      :formula="values.formula"
      :error="localOrServerError"
      :formula-type="localOrServerFormulaType"
      :table="table"
      :loading="refreshingFormula"
      :formula-type-refresh-needed="formulaTypeRefreshNeeded"
      @open-advanced-context="
        $refs.advancedFormulaEditContext.openContext($event)
      "
      @refresh-formula-type="refreshFormulaType"
    >
    </FieldFormulaInitialSubForm>
    <FormulaAdvancedEditContext
      ref="advancedFormulaEditContext"
      v-model="values.formula"
      :table="table"
      :fields="fieldsUsableInFormula"
      :error="localOrServerError"
      @blur="$v.values.formula.$touch()"
    >
    </FormulaAdvancedEditContext>
  </div>
</template>

<script>
import { required } from 'vuelidate/lib/validators'
import { mapGetters } from 'vuex'

import form from '@baserow/modules/core/mixins/form'
import { notifyIf } from '@baserow/modules/core/utils/error'

import fieldSubForm from '@baserow/modules/database/mixins/fieldSubForm'
import FieldFormulaInitialSubForm from '@baserow/modules/database/components/formula/FieldFormulaInitialSubForm'
import FormulaAdvancedEditContext from '@baserow/modules/database/components/formula/FormulaAdvancedEditContext'
import FormulaService from '@baserow/modules/database/services/formula'
import parseBaserowFormula from '@baserow/modules/database/formula/parser/parser'

export default {
  name: 'FieldFormulaSubForm',
  components: {
    FieldFormulaInitialSubForm,
    FormulaAdvancedEditContext,
  },
  mixins: [form, fieldSubForm],
  data() {
    return {
      allowedValues: ['formula'],
      values: {
        formula: '',
      },
      typeOptions: {},
      mergedTypeOptions: Object.assign({}, this.defaultValues),
      parsingError: null,
      errorFromServer: null,
      localFormulaType: null,
      localArrayFormulaType: null,
      initialFormula: null,
      refreshingFormula: false,
    }
  },
  computed: {
    ...mapGetters({
      rawFields: 'field/getAllWithPrimary',
    }),
    localOrServerFormulaType() {
      return this.localFormulaType
        ? this.localArrayFormulaType || this.localFormulaType
        : this.defaultValues.array_formula_type ||
            this.defaultValues.formula_type
    },
    fieldsUsableInFormula() {
      return this.rawFields.filter((f) => {
        const isNotThisField = f.id !== this.defaultValues.id
        const canBeReferencedByFormulaField = this.$registry
          .get('field', f.type)
          .canBeReferencedByFormulaField()
        return isNotThisField && canBeReferencedByFormulaField
      })
    },
    localOrServerError() {
      const dirty = this.$v.values.formula.$dirty
      if (dirty && !this.$v.values.formula.required) {
        return 'Please enter a formula'
      } else if (dirty && !this.$v.values.formula.parseFormula) {
        return (
          `Error in the formula on line ${this.parsingError.line} starting at
        letter ${this.parsingError.character}` +
          '\n' +
          this.toHumanReadableErrorMessage(this.parsingError)
        )
      } else if (this.errorFromServer) {
        return this.errorFromServer
      } else if (this.defaultValues.error) {
        return this.defaultValues.error
      } else {
        return null
      }
    },
    formulaChanged() {
      return (
        this.initialFormula !== null &&
        this.values.formula !== this.initialFormula
      )
    },
    updatingExistingFormula() {
      return !!this.defaultValues.id
    },
    formulaTypeRefreshNeeded() {
      return (
        this.formulaChanged &&
        !this.parsingError &&
        this.updatingExistingFormula
      )
    },
  },
  watch: {
    defaultValues(newValue, oldValue) {
      this.mergedTypeOptions = Object.assign({}, newValue)
    },
    'values.formula'(newValue, oldValue) {
      this.parseFormula(newValue)
    },
  },
  methods: {
    parseFormula(value) {
      if (value == null) {
        return false
      }
      if (!value.trim()) {
        return false
      }
      try {
        parseBaserowFormula(value)
        if (!this.initialFormula) {
          this.initialFormula = this.values.formula
        }
        this.parsingError = null
        return true
      } catch (e) {
        this.parsingError = e
        return false
      }
    },
    toHumanReadableErrorMessage(error) {
      const s = error.message
        .replace('extraneous', 'Invalid')
        .replace('input', 'letters')
        .replace(' expecting', ', was instead expecting ')
        .replace("'<EOF>'", 'the end of the formula')
        .replace('<EOF>', 'the end of the formula')
        .replace('mismatched letters', 'Unexpected')
        .replace('Unexpected the', 'Unexpected')
        .replace('SINGLEQ_STRING_LITERAL', 'a single quoted string')
        .replace('DOUBLEQ_STRING_LITERAL', 'a double quoted string')
        .replace('IDENTIFIER', 'a function')
        .replace('IDENTIFIER_UNICODE', '')
        .replace('{', '')
        .replace('}', '')
      return s + '.'
    },
    handleErrorByForm(error) {
      if (
        [
          'ERROR_WITH_FORMULA',
          'ERROR_FIELD_SELF_REFERENCE',
          'ERROR_FIELD_CIRCULAR_REFERENCE',
        ].includes(error.handler.code)
      ) {
        this.errorFromServer = error.handler.detail
        return true
      } else {
        return false
      }
    },
    reset() {
      const formula = this.values.formula
      form.methods.reset.call(this)
      this.errorFromServer = null
      this.initialFormula = formula
      this.values.formula = formula
    },
    async refreshFormulaType() {
      try {
        this.refreshingFormula = true
        const { data } = await FormulaService(this.$client).type(
          this.defaultValues.id,
          this.values.formula
        )
        // eslint-disable-next-line camelcase
        const { formula_type, array_formula_type, error, ...otherTypeOptions } =
          data

        this.mergedTypeOptions = Object.assign(
          {},
          this.mergedTypeOptions,
          otherTypeOptions
        )
        if (error) {
          this.errorFromServer = `Error with formula: ${error}.`
        } else {
          this.errorFromServer = null
        }
        // eslint-disable-next-line camelcase
        this.localFormulaType = formula_type
        // eslint-disable-next-line camelcase
        this.localArrayFormulaType = array_formula_type
      } catch (e) {
        if (!this.handleErrorByForm(e)) {
          notifyIf(e, 'field')
        }
      }
      this.initialFormula = this.values.formula
      this.refreshingFormula = false
    },
  },
  validations() {
    return {
      values: {
        formula: {
          required,
          parseFormula: this.parseFormula,
        },
      },
    }
  },
}
</script>
