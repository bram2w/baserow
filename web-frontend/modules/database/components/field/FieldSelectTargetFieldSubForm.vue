<template>
  <div>
    <div v-if="loading" class="context--loading">
      <div class="loading"></div>
    </div>
    <div
      v-else-if="fieldsInThroughTable.length > 0 && isSelectedFieldAccessible"
      class="control"
    >
      <label class="control__label control__label--small">
        {{ label }}
      </label>
      <div class="control__elements">
        <Dropdown
          v-model="values.target_field_id"
          :class="{ 'dropdown--error': $v.values.target_field_id.$error }"
          @hide="$v.values.target_field_id.$touch()"
          @input="targetFieldChanged($event)"
        >
          <DropdownItem
            v-for="field in fieldsInThroughTable"
            :key="field.id"
            :name="field.name"
            :value="field.id"
            :icon="field.icon"
          ></DropdownItem>
        </Dropdown>
      </div>
      <div v-if="$v.values.target_field_id.$error" class="error">
        {{ $t('error.requiredField') }}
      </div>
    </div>
  </div>
</template>

<script>
import { required } from 'vuelidate/lib/validators'

import form from '@baserow/modules/core/mixins/form'
import FieldService from '@baserow/modules/database/services/field'
import { notifyIf } from '@baserow/modules/core/utils/error'

export default {
  name: 'FieldSelectTargetFieldSubForm',
  mixins: [form],
  props: {
    database: {
      type: Object,
      required: true,
    },
    table: {
      type: Object,
      required: true,
    },
    throughField: {
      validator: (prop) => typeof prop === 'object' || prop === null,
      required: false,
      default: null,
    },
    label: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      allowedValues: ['target_field_id'],
      values: {
        target_field_id: null,
      },
      loading: false,
      fieldsInThroughTable: [],
    }
  },
  computed: {
    linkedToTable() {
      return this.database.tables.find(
        (table) => table.id === this.throughField?.link_row_table_id
      )
    },
    isSelectedFieldAccessible() {
      return (
        this.linkedToTable &&
        this.$hasPermission(
          'database.table.list_fields',
          this.linkedToTable,
          this.database.workspace.id
        )
      )
    },
  },
  watch: {
    throughField(value) {
      this.throughFieldChanged(value)
    },
  },
  methods: {
    async fetchFields() {
      this.loading = true

      try {
        const { data } = await FieldService(this.$client).fetchAll(
          this.throughField.link_row_table_id
        )
        this.fieldsInThroughTable = data
          .filter((f) => {
            // Filter out any links back to this table as it is a lookup back to
            // ourselve and hence would always cause a circular reference.
            return this.table.id !== f.link_row_table_id
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
      } catch (error) {
        notifyIf(error, 'view')
      }

      this.loading = false
    },
    async throughFieldChanged(value) {
      this.fieldsInThroughTable = []

      if (value === null) {
        this.values.target_field_id = null
        this.loading = false
        return
      }

      await this.fetchFields()
      this.targetFieldChanged(this.values.target_field_id)
    },
    targetFieldChanged(fieldId) {
      const field = this.fieldsInThroughTable.find((f) => f.id === fieldId)
      if (field === undefined) {
        this.values.target_field_id = null
        this.$emit('input', null)
      } else {
        this.$emit('input', field)
      }
    },
  },
  validations: {
    values: {
      target_field_id: { required },
    },
  },
}
</script>
