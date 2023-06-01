<template>
  <div>
    <div class="control">
      <Alert v-if="linkRowFieldsInThisTable.length === 0" minimal type="error">
        {{ $t('fieldCountSubForm.noTable') }}
      </Alert>
      <div v-if="linkRowFieldsInThisTable.length > 0">
        <label class="control__label control__label--small">
          {{ $t('fieldCountSubForm.selectThroughFieldLabel') }}
        </label>
        <div class="control__elements">
          <div class="control">
            <Dropdown
              v-model="values.through_field_id"
              :class="{ 'dropdown--error': $v.values.through_field_id.$error }"
              @hide="$v.values.through_field_id.$touch()"
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
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { required } from 'vuelidate/lib/validators'

import form from '@baserow/modules/core/mixins/form'
import fieldSubForm from '@baserow/modules/database/mixins/fieldSubForm'
import { DatabaseApplicationType } from '@baserow/modules/database/applicationTypes'

export default {
  name: 'FieldCountSubForm',
  mixins: [form, fieldSubForm],
  data() {
    return {
      allowedValues: ['through_field_id'],
      values: {
        through_field_id: null,
      },
    }
  },
  computed: {
    linkRowFieldsInThisTable() {
      const fields = this.$store.getters['field/getAll']
      return fields
        .filter((f) => f.type === 'link_row')
        .map((f) => {
          const fieldType = this.$registry.get('field', f.type)
          f.icon = fieldType.getIconClass()
          f.disabled = !this.tableIdsAccessible.includes(f.link_row_table_id)
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
    tableIdsAccessible() {
      return this.allTables.map((table) => table.id)
    },
  },
  validations: {
    values: {
      through_field_id: { required },
    },
  },
  methods: {
    isValid() {
      return (
        form.methods.isValid().call(this) &&
        this.linkRowFieldsInThisTable.length > 0
      )
    },
  },
}
</script>
