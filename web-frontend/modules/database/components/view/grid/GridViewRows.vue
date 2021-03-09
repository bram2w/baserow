<template>
  <div
    class="grid-view__rows"
    :style="{ transform: `translateY(${rowsTop}px)` }"
  >
    <GridViewRow
      v-for="row in rows"
      :key="'row-' + '-' + row.id"
      :row="row"
      :fields="fields"
      :field-widths="fieldWidths"
      :include-row-details="includeRowDetails"
      v-on="$listeners"
    ></GridViewRow>
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
    table: {
      type: Object,
      required: true,
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
  },
  computed: {
    fieldWidths() {
      const fieldWidths = {}
      this.fields.forEach((field) => {
        fieldWidths[field.id] = this.getFieldWidth(field.id)
      })
      return fieldWidths
    },
    ...mapGetters({
      rows: 'view/grid/getRows',
      rowsTop: 'view/grid/getRowsTop',
    }),
  },
}
</script>
