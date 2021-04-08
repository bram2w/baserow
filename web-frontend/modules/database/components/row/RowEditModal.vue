<template>
  <Modal ref="modal" @hidden="$emit('hidden', { row })">
    <h2 v-if="primary !== undefined" class="box__title">
      {{ getHeading(primary, row) }}
    </h2>
    <RowEditModalField
      v-for="field in getFields(fields, primary)"
      :ref="'field-' + field.id"
      :key="'row-edit-field-' + field.id"
      :table="table"
      :field="field"
      :row="row"
      :read-only="readOnly"
      @update="update"
      @field-updated="$emit('field-updated', $event)"
      @field-deleted="$emit('field-deleted')"
    ></RowEditModalField>
    <div v-if="!readOnly" class="actions">
      <a
        ref="createFieldContextLink"
        @click="$refs.createFieldContext.toggle($refs.createFieldContextLink)"
      >
        <i class="fas fa-plus"></i>
        add field
      </a>
      <CreateFieldContext
        ref="createFieldContext"
        :table="table"
      ></CreateFieldContext>
    </div>
  </Modal>
</template>

<script>
import modal from '@baserow/modules/core/mixins/modal'
import RowEditModalField from '@baserow/modules/database/components/row/RowEditModalField'
import CreateFieldContext from '@baserow/modules/database/components/field/CreateFieldContext'

export default {
  name: 'RowEditModal',
  components: {
    RowEditModalField,
    CreateFieldContext,
  },
  mixins: [modal],
  props: {
    table: {
      type: Object,
      required: true,
    },
    primary: {
      type: Object,
      required: false,
      default: undefined,
    },
    fields: {
      type: Array,
      required: true,
    },
    rows: {
      type: Array,
      required: true,
    },
    readOnly: {
      type: Boolean,
      required: true,
    },
  },
  data() {
    return {
      rowId: -1,
    }
  },
  computed: {
    /**
     * We need an array containing all available rows because then we can always find
     * the most up to the date row based on the provided id. We need to do it this way
     * because it is possible that the rows are refreshed after for example a field
     * update and we always need the most up to date row. This way eventually prevents
     * incompatible row values.
     *
     * Small side effect is that if the user is editing a row via the modal and another
     * user changes the filters of the same view, then the rows are refreshed for both
     * users. If the current row is then not in the buffer anymore then the modal does
     * not have a data source anymore and is forced to close. This is, in my opinion,
     * less bad compared to old/incompatible data after the user changes the field
     * type.
     */
    row() {
      const row = this.rows.find((row) => row.id === this.rowId)
      if (row === undefined) {
        // If the row is not found in the provided rows then we don't have a row data
        // source anymore which means we can close the modal.
        if (
          this.$refs &&
          Object.prototype.hasOwnProperty.call(this.$refs, 'modal') &&
          this.$refs.modal.open
        ) {
          this.$nextTick(() => {
            this.hide()
          })
        }
        return {}
      }
      return row
    },
  },
  methods: {
    show(rowId, ...args) {
      this.rowId = rowId
      this.getRootModal().show(...args)
    },
    hide(...args) {
      this.getRootModal().hide(...args)
    },
    /**
     * Because the modal can't update values by himself, an event will be called to
     * notify the parent component to actually update the value.
     */
    update(context) {
      context.table = this.table
      this.$emit('update', context)
    },
    getFields(fields, primary) {
      return primary !== undefined ? [primary].concat(fields) : fields
    },
    getHeading(primary, row) {
      const name = `field_${primary.id}`
      if (Object.prototype.hasOwnProperty.call(row, name)) {
        return this.$registry
          .get('field', primary.type)
          .toHumanReadableString(primary, row[name])
      } else {
        return null
      }
    },
  },
}
</script>
