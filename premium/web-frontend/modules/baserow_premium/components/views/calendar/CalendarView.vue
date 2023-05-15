<template>
  <div class="calendar-view">
    <CalendarMonth
      :fields="fields"
      :store-prefix="storePrefix"
      :loading="loading"
      :read-only="readOnly"
      :database="database"
      :table="table"
      @edit-row="openRowEditModal($event.id)"
      @create-row="openCreateRowModal"
    ></CalendarMonth>
    <RowCreateModal
      ref="rowCreateModal"
      :database="database"
      :table="table"
      :primary-is-sortable="true"
      :visible-fields="visibleCardFields"
      :hidden-fields="hiddenFields"
      :show-hidden-fields="showHiddenFieldsInRowModal"
      @toggle-hidden-fields-visibility="
        showHiddenFieldsInRowModal = !showHiddenFieldsInRowModal
      "
      @created="createRow"
      @order-fields="orderFields"
      @toggle-field-visibility="toggleFieldVisibility"
      @field-updated="$emit('refresh', $event)"
      @field-deleted="$emit('refresh')"
    ></RowCreateModal>
    <RowEditModal
      ref="rowEditModal"
      enable-navigation
      :database="database"
      :table="table"
      :primary-is-sortable="false"
      :visible-fields="visibleCardFields"
      :hidden-fields="hiddenFields"
      :rows="allRows"
      :read-only="
        readOnly ||
        !$hasPermission(
          'database.table.update_row',
          table,
          database.workspace.id
        )
      "
      :show-hidden-fields="showHiddenFieldsInRowModal"
      @hidden="$emit('selected-row', undefined)"
      @toggle-hidden-fields-visibility="
        showHiddenFieldsInRowModal = !showHiddenFieldsInRowModal
      "
      @update="updateValue"
      @order-fields="orderFields"
      @toggle-field-visibility="toggleFieldVisibility"
      @field-updated="$emit('refresh', $event)"
      @field-deleted="$emit('refresh')"
      @field-created="
        fieldCreated($event)
        showHiddenFieldsInRowModal = true
      "
      @navigate-previous="$emit('navigate-previous', $event)"
      @navigate-next="$emit('navigate-next', $event)"
    ></RowEditModal>
  </div>
</template>
<script>
import CalendarMonth from '@baserow_premium/components/views/calendar/CalendarMonth'
import {
  filterHiddenFieldsFunction,
  filterVisibleFieldsFunction,
  sortFieldsByOrderAndIdFunction,
} from '@baserow/modules/database/utils/view'
import { mapGetters } from 'vuex'
import { notifyIf } from '@baserow/modules/core/utils/error'
import viewHelpers from '@baserow/modules/database/mixins/viewHelpers'
import RowEditModal from '@baserow/modules/database/components/row/RowEditModal.vue'
import { populateRow } from '@baserow/modules/database/store/view/grid'
import { clone } from '@baserow/modules/core/utils/object'
import RowCreateModal from '@baserow/modules/database/components/row/RowCreateModal.vue'

export default {
  name: 'CalendarView',
  components: {
    CalendarMonth,
    RowEditModal,
    RowCreateModal,
  },
  mixins: [viewHelpers],
  props: {
    database: {
      type: Object,
      required: true,
    },
    table: {
      type: Object,
      required: true,
    },
    view: {
      type: Object,
      required: true,
    },
    fields: {
      type: Array,
      required: true,
    },
    readOnly: {
      type: Boolean,
      required: true,
    },
    loading: {
      type: Boolean,
      required: true,
    },
    storePrefix: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      showHiddenFieldsInRowModal: false,
    }
  },
  computed: {
    visibleCardFields() {
      return this.fields
        .filter(filterVisibleFieldsFunction(this.fieldOptions))
        .sort(sortFieldsByOrderAndIdFunction(this.fieldOptions))
    },
    hiddenFields() {
      return this.fields
        .filter(filterHiddenFieldsFunction(this.fieldOptions))
        .sort(sortFieldsByOrderAndIdFunction(this.fieldOptions))
    },
  },
  watch: {
    row: {
      deep: true,
      handler(row) {
        if (row !== null && this.$refs.rowEditModal) {
          this.populateAndEditRow(row)
        }
      },
    },
  },
  mounted() {
    if (this.row !== null) {
      this.populateAndEditRow(this.row)
    }
  },
  beforeCreate() {
    this.$options.computed = {
      ...(this.$options.computed || {}),
      ...mapGetters({
        row: 'rowModalNavigation/getRow',
        allRows:
          this.$options.propsData.storePrefix + 'view/calendar/getAllRows',
        fieldOptions:
          this.$options.propsData.storePrefix +
          'view/calendar/getAllFieldOptions',
        getDateField:
          this.$options.propsData.storePrefix + 'view/calendar/getDateField',
      }),
    }
  },
  methods: {
    async updateValue({ field, row, value, oldValue }) {
      try {
        await this.$store.dispatch(
          this.storePrefix + 'view/calendar/updateRowValue',
          {
            table: this.table,
            view: this.view,
            fields: this.fields,
            row,
            field,
            value,
            oldValue,
          }
        )
      } catch (error) {
        notifyIf(error, 'field')
      }
    },
    /**
     * When the row edit modal is opened we notifiy
     * the Table component that a new row has been selected,
     * such that we can update the path to include the row id.
     */
    openRowEditModal(rowId) {
      this.$refs.rowEditModal.show(rowId)
      this.$emit('selected-row', rowId)
    },
    /**
     * Populates a new row and opens the row edit modal
     * to edit the row.
     */
    populateAndEditRow(row) {
      const rowClone = populateRow(clone(row))
      this.$store.dispatch(this.storePrefix + 'view/calendar/selectRow', {
        row: rowClone,
        fields: this.fields,
      })

      this.$refs.rowEditModal.show(row.id, rowClone)
    },
    async createRow({ row, callback }) {
      try {
        await this.$store.dispatch(
          this.storePrefix + 'view/calendar/createNewRow',
          {
            view: this.view,
            table: this.table,
            fields: this.fields,
            values: row,
          }
        )
        callback()
      } catch (error) {
        callback(error)
      }
    },

    openCreateRowModal(event) {
      const defaults = {}
      const dateField = this.getDateField(this.fields)
      const fieldType = this.$registry.get('field', dateField.type)
      if (event?.day?.date != null && dateField && !fieldType.getIsReadOnly()) {
        const name = `field_${dateField.id}`
        if (dateField.date_include_time) {
          defaults[name] = event.day.date.toISOString()
        } else {
          defaults[name] = event.day.date.format('YYYY-MM-DD')
        }
      }
      this.$refs.rowCreateModal.show(defaults)
    },
  },
}
</script>
