<template>
  <RowEditModal
    ref="modal"
    :read-only="readOnly"
    :database="database"
    :table="table"
    :rows="[]"
    :fields="fields"
    :visible-fields="fields"
    :fields-sortable="fieldsSortable"
    :can-modify-fields="canModifyFields"
    @hidden="$emit('hidden', $event)"
    @update="update"
  ></RowEditModal>
</template>

<script>
import { DatabaseApplicationType } from '@baserow/modules/database/applicationTypes'
import RowEditModal from '@baserow/modules/database/components/row/RowEditModal'
import FieldService from '@baserow/modules/database/services/field'
import RowService from '@baserow/modules/database/services/row'
import { populateField } from '@baserow/modules/database/store/field'
import { notifyIf } from '@baserow/modules/core/utils/error'

/**
 * This component can open the row edit modal having the fields of that table in the
 * fields store. It will make a request to the backend fetching the missing
 * information.
 */
export default {
  name: 'ForeignRowEditModal',
  components: { RowEditModal },
  props: {
    tableId: {
      type: Number,
      required: true,
    },
    fieldsSortable: {
      type: Boolean,
      required: false,
      default: () => true,
    },
    canModifyFields: {
      type: Boolean,
      required: false,
      default: () => true,
    },
    readOnly: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  data() {
    return {
      fetchedTableAndFields: false,
      table: {},
      fields: [],
    }
  },
  computed: {
    database() {
      const databaseType = DatabaseApplicationType.getType()
      for (const application of this.$store.getters['application/getAll']) {
        if (application.type !== databaseType) {
          continue
        }

        const foundTable = application.tables.find(
          ({ id }) => id === this.tableId
        )

        if (foundTable) {
          return application
        }
      }

      return undefined
    },
  },
  methods: {
    async fetchTableAndFields() {
      // Find the table in the applications to prevent a request to the backend and to
      // maintain reactivity with the real time updates.
      const databaseType = DatabaseApplicationType.getType()
      for (const application of this.$store.getters['application/getAll']) {
        if (application.type !== databaseType) {
          continue
        }

        const foundTable = application.tables.find(
          ({ id }) => id === this.tableId
        )

        if (foundTable) {
          this.table = foundTable
          break
        }
      }

      // Because we don't have the fields in the store we need to fetch those for this
      // table.
      const { data: fieldData } = await FieldService(this.$client).fetchAll(
        this.tableId
      )
      fieldData.forEach((part, index) => {
        populateField(fieldData[index], this.$registry)
      })
      this.fields = fieldData

      // Mark the table and fields as fetched, so that we don't have to do that a
      // second time when the user opens another row.
      this.fetchedTableAndFields = true
    },

    async show(rowId) {
      if (!this.fetchedTableAndFields) {
        await this.fetchTableAndFields()
      }

      const { data: rowData } = await RowService(this.$client).get(
        this.tableId,
        rowId
      )
      this.$refs.modal.show(rowData.id, rowData)
    },
    /**
     * A method which listens for `update` event emitted by other components
     * (f. ex. RowEditModalFieldsList). It updates the foreign row that's being
     * edited in a real-time manner.
     */
    async update({ field, row, value, oldValue, table }) {
      // Get the field type (f. ex. DateFieldType, URLFieldType) and old / new
      // values(s) for the field that's being updated and prepare them for update:
      const fieldType = this.$registry.get('field', field._.type.type)
      const newValues = { id: row.id }
      const newValuesForUpdate = {}
      const oldValues = { id: row.id }
      const fieldName = `field_${field.id}`
      newValues[fieldName] = value
      newValuesForUpdate[fieldName] = fieldType.prepareValueForUpdate(
        field,
        value
      )
      oldValues[fieldName] = oldValue

      // Loop through all of the fields in the ForeignRowEditModal and try
      // to determine the changed value, and, if it changed, add it to the newValues
      // dict. Also add the `old` (current) field value to the oldValues dict
      // to be able to restore it if something fails:
      this.fields.forEach((fieldToCall) => {
        const fieldType = this.$registry.get('field', fieldToCall._.type.type)
        const fieldToCallName = `field_${fieldToCall.id}`
        const currentFieldValue = row[fieldToCallName]
        const optimisticFieldValue = fieldType.onRowChange(
          row,
          fieldToCall,
          currentFieldValue
        )

        if (currentFieldValue !== optimisticFieldValue) {
          newValues[fieldToCallName] = optimisticFieldValue
          oldValues[fieldToCallName] = currentFieldValue
        }
      })

      this.$store.dispatch('rowModal/updated', {
        tableId: this.tableId,
        values: newValues,
      })

      // Attempt to call the `rowModal/updated` action in the store which is
      // usually called when we receive a real time row update event, this updates
      // the foreign row that's being edited in a real-time manner:
      try {
        const { data } = await RowService(this.$client).update(
          table.id,
          row.id,
          newValuesForUpdate
        )
        this.$store.dispatch('rowModal/updated', {
          tableId: this.tableId,
          values: data,
        })
        this.$emit('refresh-row')
        // In case the above fails, previous row values should be restored:
      } catch (error) {
        this.$store.dispatch('rowModal/updated', {
          tableId: this.tableId,
          values: oldValues,
        })
        notifyIf(error, 'row')
      }
    },
  },
}
</script>
