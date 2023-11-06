<template>
  <div
    class="grid-view__rows"
    :style="{
      transform: `translateY(${rowsTop}px) translateX(${leftOffset || 0}px)`,
    }"
  >
    <GridViewRow
      v-for="(row, index) in rows"
      :key="`row-${row._.persistentId}`"
      :groups="groupsPerRow[row.id]"
      :view="view"
      :workspace-id="workspaceId"
      :row="row"
      :rendered-fields="renderedFields"
      :visible-fields="visibleFields"
      :all-fields-in-table="allFieldsInTable"
      :primary-field-is-sticky="primaryFieldIsSticky"
      :field-widths="fieldWidths"
      :include-row-details="includeRowDetails"
      :include-group-by="includeGroupBy"
      :decorations-by-place="decorationsByPlace"
      :read-only="readOnly"
      :can-drag="view.sortings.length === 0 && activeGroupBys.length === 0"
      :store-prefix="storePrefix"
      :row-identifier-type="view.row_identifier_type"
      :count="index + rowsStartIndex + bufferStartIndex + 1"
      v-on="$listeners"
    />
  </div>
</template>

<script>
import { mapGetters } from 'vuex'

import GridViewRow from '@baserow/modules/database/components/view/grid/GridViewRow'
import gridViewHelpers from '@baserow/modules/database/mixins/gridViewHelpers'

export default {
  name: 'GridViewRows',
  components: { GridViewRow },
  mixins: [gridViewHelpers],
  props: {
    /**
     * The visible fields that are within the viewport. The other ones are not rendered
     * for performance reasons.
     */
    renderedFields: {
      type: Array,
      required: true,
    },
    /**
     * The fields that are chosen to be visible within the view.
     */
    visibleFields: {
      type: Array,
      required: true,
    },
    /**
     * All the fields in the table, regardless of the visibility, or whether they
     * should be rendered.
     */
    allFieldsInTable: {
      type: Array,
      required: true,
    },
    decorationsByPlace: {
      type: Object,
      required: true,
    },
    leftOffset: {
      type: Number,
      required: false,
      default: 0,
    },
    view: {
      type: Object,
      required: true,
    },
    includeRowDetails: {
      type: Boolean,
      required: false,
      default: () => false,
    },
    includeGroupBy: {
      type: Boolean,
      required: false,
      default: () => false,
    },
    readOnly: {
      type: Boolean,
      required: true,
    },
    workspaceId: {
      type: Number,
      required: true,
    },
    primaryFieldIsSticky: {
      type: Boolean,
      required: false,
      default: () => true,
    },
  },
  computed: {
    fieldWidths() {
      const fieldWidths = {}
      this.visibleFields.forEach((field) => {
        fieldWidths[field.id] = this.getFieldWidth(field.id)
      })
      return fieldWidths
    },
    /**
     * This computed property prepares an array with clear instructions on the groups
     * for each row. It will hold data whether the row is the start of a group, or the
     * end, and for which group that is.
     *
     * We're calculating this for all the rows in the buffer because that way we can
     * immediately render the correct borders of the rows, even if the user is
     * scrolling fast through them.
     *
     * It returns a structure like:
     *
     * {
     *   [rowId]: [
     *     {
     *       id: groupById,
     *       start: false,
     *       end: true,
     *       groupBy: {}
     *     }
     *   ]
     * }
     */
    groupsPerRow() {
      const groupBys = this.activeGroupBys
      const rows = this.allRows
      const groups = {}
      const fieldTypeMap = {}
      const fieldMap = {}

      rows.forEach((row, index) => {
        const previousRow = rows[index - 1]
        const nextRow = rows[index + 1]

        let lastGroupStart = false
        let lastGroupEnd = false

        const startEndPerGroup = groupBys.map((groupBy) => {
          let start = false // The start of a group based on the group by value.
          let end = false // The end of a group based on the group by value.
          let fieldType = fieldTypeMap[groupBy.field]
          let field = fieldMap[groupBy.field]

          if (fieldType === undefined) {
            field = this.allFieldsInTable.find((f) => f.id === groupBy.field)
            fieldType = this.$registry.get('field', field.type)
            fieldMap[groupBy.field] = field
            fieldTypeMap[groupBy.field] = fieldType
          }

          if (
            previousRow === undefined ||
            !fieldType.isEqual(
              field,
              previousRow[`field_${groupBy.field}`],
              row[`field_${groupBy.field}`]
            ) ||
            lastGroupStart
          ) {
            start = true
          }

          if (
            nextRow === undefined ||
            !fieldType.isEqual(
              field,
              nextRow[`field_${groupBy.field}`],
              row[`field_${groupBy.field}`]
            ) ||
            lastGroupEnd
          ) {
            end = true
          }

          lastGroupStart = start
          lastGroupEnd = end

          return {
            id: groupBy.id,
            start,
            end,
            groupBy,
          }
        })

        groups[row.id] = startEndPerGroup
      })
      return groups
    },
  },
  beforeCreate() {
    this.$options.computed = {
      ...(this.$options.computed || {}),
      ...mapGetters({
        rows: this.$options.propsData.storePrefix + 'view/grid/getRows',
        allRows: this.$options.propsData.storePrefix + 'view/grid/getAllRows',
        rowsTop: this.$options.propsData.storePrefix + 'view/grid/getRowsTop',
        rowsStartIndex:
          this.$options.propsData.storePrefix + 'view/grid/getRowsStartIndex',
        bufferStartIndex:
          this.$options.propsData.storePrefix + 'view/grid/getBufferStartIndex',
        activeGroupBys:
          this.$options.propsData.storePrefix + 'view/grid/getActiveGroupBys',
      }),
    }
  },
}
</script>
