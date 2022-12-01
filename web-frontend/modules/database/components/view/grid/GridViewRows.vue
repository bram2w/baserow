<template>
  <div
    class="grid-view__rows"
    :style="{
      transform: `translateY(${rowsTop}px) translateX(${leftOffset}px)`,
    }"
  >
    <GridViewRow
      v-for="(row, index) in rows"
      :key="`row-${row.id}`"
      :view="view"
      :group-id="groupId"
      :row="row"
      :fields="fields"
      :all-fields="allFields"
      :field-widths="fieldWidths"
      :include-row-details="includeRowDetails"
      :decorations-by-place="decorationsByPlace"
      :read-only="readOnly"
      :can-drag="view.sortings.length === 0"
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
    fields: {
      type: Array,
      required: true,
    },
    allFields: {
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
    readOnly: {
      type: Boolean,
      required: true,
    },
    groupId: {
      type: Number,
      required: true,
    },
  },
  computed: {
    fieldWidths() {
      const fieldWidths = {}
      this.allFields.forEach((field) => {
        fieldWidths[field.id] = this.getFieldWidth(field.id)
      })
      return fieldWidths
    },
  },
  beforeCreate() {
    this.$options.computed = {
      ...(this.$options.computed || {}),
      ...mapGetters({
        rows: this.$options.propsData.storePrefix + 'view/grid/getRows',
        rowsTop: this.$options.propsData.storePrefix + 'view/grid/getRowsTop',
        rowsStartIndex:
          this.$options.propsData.storePrefix + 'view/grid/getRowsStartIndex',
        bufferStartIndex:
          this.$options.propsData.storePrefix + 'view/grid/getBufferStartIndex',
      }),
    }
  },
}
</script>
