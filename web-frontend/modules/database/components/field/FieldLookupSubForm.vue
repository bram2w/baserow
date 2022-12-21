<template>
  <div>
    <div class="control">
      <Alert v-if="linkRowFieldsInThisTable.length === 0" minimal type="error">
        {{ $t('fieldLookupSubForm.noTable') }}
      </Alert>
      <div v-if="linkRowFieldsInThisTable.length > 0">
        <label class="control__label control__label--small">
          {{ $t('fieldLookupSubForm.selectThroughFieldLabel') }}
        </label>
        <div class="control__elements">
          <div class="control">
            <Dropdown
              v-model="values.through_field_id"
              :class="{ 'dropdown--error': $v.values.through_field_id.$error }"
              @hide="$v.values.through_field_id.$touch()"
              @input="throughFieldSelected"
            >
              <DropdownItem
                v-for="field in linkRowFieldsInThisTable"
                :key="field.id"
                :disabled="field.disabled"
                :name="field.name"
                :value="field.id"
                :icon="field.icon"
              ></DropdownItem>
            </Dropdown>
            <div v-if="$v.values.through_field_id.$error" class="error">
              {{ $t('error.requiredField') }}
            </div>
          </div>
          <div v-if="loading" class="context--loading">
            <div class="loading"></div>
          </div>
          <div v-else-if="fieldsInThroughTable.length > 0" class="control">
            <label class="control__label control__label--small">
              {{ $t('fieldLookupSubForm.selectTargetFieldLabel') }}
            </label>
            <Dropdown
              v-model="values.target_field_id"
              :class="{ 'dropdown--error': $v.values.target_field_id.$error }"
              @hide="$v.values.target_field_id.$touch()"
            >
              <DropdownItem
                v-for="field in fieldsInThroughTable"
                :key="field.id"
                :name="field.name"
                :value="field.id"
                :icon="field.icon"
              ></DropdownItem>
            </Dropdown>
            <div
              v-if="values.through_field_id && $v.values.target_field_id.$error"
              class="error"
            >
              {{ $t('error.requiredField') }}
            </div>
          </div>
          <template v-if="values.target_field_id">
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
      </div>
    </div>
  </div>
</template>

<script>
import { required } from 'vuelidate/lib/validators'

import form from '@baserow/modules/core/mixins/form'
import fieldSubForm from '@baserow/modules/database/mixins/fieldSubForm'
import { notifyIf } from '@baserow/modules/core/utils/error'
import FieldService from '@baserow/modules/database/services/field'
import FormulaTypeSubForms from '@baserow/modules/database/components/formula/FormulaTypeSubForms'
import { DatabaseApplicationType } from '@baserow/modules/database/applicationTypes'

export default {
  name: 'FieldLookupSubForm',
  components: {
    FormulaTypeSubForms,
  },
  mixins: [form, fieldSubForm],
  data() {
    return {
      allowedValues: ['through_field_id', 'target_field_id'],
      values: {
        through_field_id: null,
        target_field_id: null,
      },
      loading: false,
      errorFromServer: null,
      fieldsInThroughTable: [],
    }
  },
  computed: {
    linkRowFieldsInThisTable() {
      const tableIdsAccessible = this.allTables.map((table) => table.id)
      const fields = this.$store.getters['field/getAll']
      return fields
        .filter((f) => f.type === 'link_row')
        .map((f) => {
          const fieldType = this.$registry.get('field', f.type)
          f.icon = fieldType.getIconClass()
          f.disabled = !tableIdsAccessible.includes(f.link_row_table_id)
          return f
        })
    },
    allTables() {
      const databaseType = DatabaseApplicationType.getType()
      return this.$store.getters['application/getAll'].reduce(
        (tables, application) => {
          if (application.type === databaseType) {
            return tables.concat(application.tables || [])
          }
          return tables
        },
        []
      )
    },
    targetFieldFormulaType() {
      if (this.values.target_field_id) {
        const targetFieldIndex = this.fieldsInThroughTable.findIndex(
          (f) => f.id === this.values.target_field_id
        )
        if (targetFieldIndex >= 0) {
          const targetField = this.fieldsInThroughTable[targetFieldIndex]
          return targetField.array_formula_type || targetField.type
        }
      }
      return 'unknown'
    },
  },
  watch: {
    'defaultValues.through_field_id'() {
      this.throughFieldSelected()
    },
    'values.through_field_id'() {
      this.throughFieldSelected()
    },
    selectedField() {
      this.throughFieldSelected()
    },
  },
  created() {
    this.throughFieldSelected()
  },
  validations: {
    values: {
      through_field_id: { required },
      target_field_id: { required },
    },
  },
  methods: {
    async throughFieldSelected() {
      if (!this.values.through_field_id) {
        return
      }
      this.loading = true
      this.fieldsInThroughTable = []
      this.errorFromServer = null

      try {
        const selectedField = this.$store.getters['field/get'](
          this.values.through_field_id
        )
        if (selectedField && selectedField.link_row_table_id) {
          const { data } = await FieldService(this.$client).fetchAll(
            selectedField.link_row_table_id
          )
          this.fieldsInThroughTable = data
            .filter((f) => {
              // If we are the primary field filter out any links back to this table
              // as it is a lookup back to ourself and hence would always cause a
              // circular reference.
              return (
                !this.defaultValues.primary ||
                this.defaultValues.table_id !== f.link_row_table_id
              )
            })
            .filter((f) => {
              return this.$registry
                .get('field', f.type)
                .canBeReferencedByFormulaField()
            })
            .map((f) => {
              const fieldType = this.$registry.get('field', f.type)
              f.icon = fieldType.getIconClass()
              return f
            })
        }
      } catch (error) {
        notifyIf(error, 'view')
      }

      this.loading = false
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
    isValid() {
      return (
        form.methods.isValid().call(this) &&
        this.linkRowFieldsInThisTable.length > 0
      )
    },
    reset() {
      form.methods.reset.call(this)
      this.errorFromServer = null
    },
  },
}
</script>
