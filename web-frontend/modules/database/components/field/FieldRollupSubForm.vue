<template>
  <div>
    <FieldSelectThroughFieldSubForm
      :fields="fields"
      :database="database"
      :default-values="defaultValues"
      @input="selectedThroughField = $event"
    ></FieldSelectThroughFieldSubForm>
    <FieldSelectTargetFieldSubForm
      :database="database"
      :table="table"
      :through-field="selectedThroughField"
      :default-values="defaultValues"
      :label="$t('fieldRollupSubForm.selectTargetFieldLabel')"
      @input="selectedTargetField = $event"
    ></FieldSelectTargetFieldSubForm>
    <template v-if="selectedTargetField">
      <div class="control">
        <label class="control__label control__label--small">{{
          $t('fieldRollupSubForm.label')
        }}</label>
        <div class="control__elements">
          <FixedItemsDropdown
            v-model="values.rollup_function"
            :class="{ 'dropdown--error': $v.values.rollup_function.$error }"
            @hide="$v.values.rollup_function.$touch()"
          >
            <DropdownItem
              v-for="f in rollupFunctions"
              :key="f.getType()"
              :name="f.getType()"
              :value="f.getType()"
              :description="f.getDescription()"
            ></DropdownItem>
          </FixedItemsDropdown>
        </div>
      </div>
      <FormulaTypeSubForms
        :default-values="defaultValues"
        :formula-type="targetFieldFormulaType"
        :table="table"
      >
      </FormulaTypeSubForms>
    </template>
    <div v-if="errorFromServer" class="error formula-field__error">
      {{ errorFromServer }}
    </div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import { required } from 'vuelidate/lib/validators'

import form from '@baserow/modules/core/mixins/form'
import fieldSubForm from '@baserow/modules/database/mixins/fieldSubForm'
import FormulaTypeSubForms from '@baserow/modules/database/components/formula/FormulaTypeSubForms'
import FieldSelectThroughFieldSubForm from '@baserow/modules/database/components/field/FieldSelectThroughFieldSubForm'
import FieldSelectTargetFieldSubForm from '@baserow/modules/database/components/field/FieldSelectTargetFieldSubForm'
import FixedItemsDropdown from '@baserow/modules/core/components/FixedItemsDropdown'

export default {
  name: 'FieldRollupSubForm',
  components: {
    FixedItemsDropdown,
    FieldSelectThroughFieldSubForm,
    FieldSelectTargetFieldSubForm,
    FormulaTypeSubForms,
  },
  mixins: [form, fieldSubForm],
  data() {
    return {
      selectedThroughField: null,
      selectedTargetField: null,
      allowedValues: ['rollup_function'],
      values: {
        rollup_function: null,
      },
      errorFromServer: null,
    }
  },
  computed: {
    database() {
      return this.$store.getters['application/get'](this.table.database_id)
    },
    targetFieldFormulaType() {
      if (this.selectedTargetField) {
        return (
          this.selectedTargetField.array_formula_type ||
          this.selectedTargetField.type
        )
      }
      return 'unknown'
    },
    rollupFunctions() {
      return Object.values(this.$registry.getAll('formula_function')).filter(
        (f) => f.isRollupCompatible()
      )
    },
    ...mapGetters({
      // This part might fail in the future because we can't 100% depend on that the
      // fields in the store are related to the component that renders this. An example
      // is if you edit the field type in a row edit modal of a related table.
      fields: 'field/getAll',
    }),
  },
  validations: {
    values: {
      rollup_function: { required },
    },
  },
  methods: {
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
      form.methods.reset.call(this)
      this.errorFromServer = null
    },
  },
}
</script>
