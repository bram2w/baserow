<template>
  <div>
    <div class="grid-view__inner" :style="{ 'min-width': width + 'px' }">
      <GridViewHead
        :table="table"
        :view="view"
        :fields="visibleFields"
        :include-field-width-handles="includeFieldWidthHandles"
        :include-row-details="includeRowDetails"
        :include-add-field="includeAddField"
        @refresh="$emit('refresh', $event)"
        @dragging="
          canOrderFields &&
            $refs.fieldDragging.start($event.field, $event.event)
        "
      ></GridViewHead>
      <div ref="body" class="grid-view__body">
        <div class="grid-view__body-inner">
          <GridViewPlaceholder
            :fields="visibleFields"
            :include-row-details="includeRowDetails"
          ></GridViewPlaceholder>
          <GridViewRows
            :table="table"
            :view="view"
            :fields="visibleFields"
            :include-row-details="includeRowDetails"
            v-on="$listeners"
          ></GridViewRows>
          <GridViewRowAdd
            :fields="visibleFields"
            :include-row-details="includeRowDetails"
            v-on="$listeners"
          ></GridViewRowAdd>
        </div>
      </div>
      <div class="grid-view__foot">
        <slot name="foot"></slot>
      </div>
    </div>
    <GridViewFieldDragging
      ref="fieldDragging"
      :view="view"
      :fields="visibleFields"
      :container-width="width"
      @scroll="$emit('scroll', $event)"
    ></GridViewFieldDragging>
  </div>
</template>

<script>
import GridViewHead from '@baserow/modules/database/components/view/grid/GridViewHead'
import GridViewPlaceholder from '@baserow/modules/database/components/view/grid/GridViewPlaceholder'
import GridViewRows from '@baserow/modules/database/components/view/grid/GridViewRows'
import GridViewRowAdd from '@baserow/modules/database/components/view/grid/GridViewRowAdd'
import GridViewFieldDragging from '@baserow/modules/database/components/view/grid/GridViewFieldDragging'
import gridViewHelpers from '@baserow/modules/database/mixins/gridViewHelpers'
import { GridViewType } from '@baserow/modules/database/viewTypes'

export default {
  name: 'GridViewSection',
  components: {
    GridViewHead,
    GridViewPlaceholder,
    GridViewRows,
    GridViewRowAdd,
    GridViewFieldDragging,
  },
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
    includeFieldWidthHandles: {
      type: Boolean,
      required: false,
      default: () => true,
    },
    includeRowDetails: {
      type: Boolean,
      required: false,
      default: () => false,
    },
    includeAddField: {
      type: Boolean,
      required: false,
      default: () => false,
    },
    canOrderFields: {
      type: Boolean,
      required: false,
      default: () => false,
    },
  },
  computed: {
    /**
     * Returns only the visible fields in the correct order.
     */
    visibleFields() {
      return this.fields
        .filter((field) => {
          const exists = Object.prototype.hasOwnProperty.call(
            this.fieldOptions,
            field.id
          )
          return !exists || (exists && !this.fieldOptions[field.id].hidden)
        })
        .sort((a, b) => {
          const orderA = this.fieldOptions[a.id]
            ? this.fieldOptions[a.id].order
            : GridViewType.getMaxPossibleOrderValue()
          const orderB = this.fieldOptions[b.id]
            ? this.fieldOptions[b.id].order
            : GridViewType.getMaxPossibleOrderValue()

          // First by order.
          if (orderA > orderB) {
            return 1
          } else if (orderA < orderB) {
            return -1
          }

          // Then by id.
          if (a.id < b.id) {
            return -1
          } else if (a.id > b.id) {
            return 1
          } else {
            return 0
          }
        })
    },
    /**
     * Calculates the total width of the whole section based on the fields and the
     * given options.
     */
    width() {
      let width = Object.values(this.visibleFields).reduce(
        (value, field) => this.getFieldWidth(field.id) + value,
        0
      )

      if (this.includeRowDetails) {
        width += this.gridViewRowDetailsWidth
      }

      // The add button has a width of 100 and we reserve 100 at the right side.
      if (this.includeAddField) {
        width += 100 + 100
      }

      return width
    },
  },
}
</script>
