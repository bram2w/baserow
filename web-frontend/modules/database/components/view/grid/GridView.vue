<template>
  <div v-scroll="scroll" class="grid-view">
    <Scrollbars
      ref="scrollbars"
      horizontal="right"
      vertical="rightBody"
      :style="{ left: widths.left + 'px' }"
      @vertical="verticalScroll"
      @horizontal="horizontalScroll"
    ></Scrollbars>
    <div class="grid-view-left" :style="{ width: widths.left + 'px' }">
      <div class="grid-view-inner" :style="{ width: widths.left + 'px' }">
        <div class="grid-view-head">
          <div
            class="grid-view-column"
            :style="{ width: widths.leftReserved + 'px' }"
          ></div>
          <GridViewFieldType
            v-if="primary !== null"
            :field="primary"
            :style="{ width: widths.fields[primary.id] + 'px' }"
          ></GridViewFieldType>
        </div>
        <div ref="leftBody" class="grid-view-body">
          <div class="grid-view-body-inner">
            <div
              class="grid-view-placeholder"
              :style="{
                height: placeholderHeight + 'px',
                width: widths.left + 'px',
              }"
            >
              <div
                class="grid-view-placeholder-column"
                :style="{
                  width: widths.left + 'px',
                }"
              ></div>
            </div>
            <div
              class="grid-view-rows"
              :style="{ transform: `translateY(${rowsTop}px)` }"
            >
              <div
                v-for="row in rows"
                :key="'left-row-' + view.id + '-' + row.id"
                class="grid-view-row"
                :class="{
                  'grid-view-row-loading': row._.loading,
                  'grid-view-row-hover': row._.hover,
                }"
                @mouseover="setRowHover(row, true)"
                @mouseleave="setRowHover(row, false)"
                @contextmenu.prevent="showRowContext($event, row)"
              >
                <div
                  class="grid-view-column"
                  :style="{ width: widths.leftReserved + 'px' }"
                >
                  <div class="grid-view-row-info">
                    <div class="grid-view-row-count">{{ row.id }}</div>
                    <a
                      class="grid-view-row-more"
                      @click="$refs.rowEditModal.show(row)"
                    >
                      <i class="fas fa-expand"></i>
                    </a>
                  </div>
                </div>
                <GridViewField
                  v-if="primary !== null"
                  :ref="'row-' + row.id + '-field-' + primary.id"
                  :field="primary"
                  :row="row"
                  :style="{ width: widths.fields[primary.id] + 'px' }"
                  @selected="selectedField(primary, $event.component)"
                  @selectNext="selectNextField(row, primary, fields, primary)"
                  @selectAbove="
                    selectNextField(row, primary, fields, primary, 'above')
                  "
                  @selectBelow="
                    selectNextField(row, primary, fields, primary, 'below')
                  "
                  @update="updateValue"
                ></GridViewField>
              </div>
            </div>
            <div class="grid-view-row">
              <div
                class="grid-view-column"
                :style="{ width: widths.left + 'px' }"
              >
                <a
                  class="grid-view-add-row"
                  :class="{ hover: addHover }"
                  @mouseover="addHover = true"
                  @mouseleave="addHover = false"
                  @click="addRow()"
                >
                  <i class="fas fa-plus"></i>
                </a>
              </div>
            </div>
          </div>
        </div>
        <div class="grid-view-foot">
          <div class="grid-view-column" :style="{ width: widths.left + 'px' }">
            <div class="grid-view-foot-info">{{ count }} rows</div>
          </div>
        </div>
      </div>
    </div>
    <div
      ref="divider"
      class="grid-view-divider"
      :style="{ left: widths.left + 'px' }"
    ></div>
    <GridViewFieldWidthHandle
      class="grid-view-divider-width"
      :style="{ left: widths.left + 'px' }"
      :grid="view"
      :field="primary"
      :width="widths.fields[primary.id]"
    ></GridViewFieldWidthHandle>
    <div
      ref="right"
      class="grid-view-right"
      :style="{ left: widths.left + 'px' }"
    >
      <div
        class="grid-view-inner"
        :style="{ 'min-width': widths.right + 'px' }"
      >
        <div class="grid-view-head">
          <GridViewFieldType
            v-for="field in fields"
            :key="'right-head-field-' + view.id + '-' + field.id"
            :field="field"
            :style="{ width: widths.fields[field.id] + 'px' }"
          >
            <GridViewFieldWidthHandle
              class="grid-view-description-width"
              :grid="view"
              :field="field"
              :width="widths.fields[field.id]"
            ></GridViewFieldWidthHandle>
          </GridViewFieldType>
          <div
            class="grid-view-column"
            :style="{ width: widths.rightAdd + 'px' }"
          >
            <a
              ref="createFieldContextLink"
              class="grid-view-add-column"
              @click="
                $refs.createFieldContext.toggle($refs.createFieldContextLink)
              "
            >
              <i class="fas fa-plus"></i>
            </a>
            <CreateFieldContext
              ref="createFieldContext"
              :table="table"
            ></CreateFieldContext>
          </div>
        </div>
        <div ref="rightBody" class="grid-view-body">
          <div class="grid-view-body-inner">
            <div
              class="grid-view-placeholder"
              :style="{
                height: placeholderHeight + 'px',
                width: widths.rightFieldsOnly + 'px',
              }"
            >
              <div
                v-for="(value, id) in widths.placeholderPositions"
                :key="'right-placeholder-column-' + view.id + '-' + id"
                class="grid-view-placeholder-column"
                :style="{ left: value - 1 + 'px' }"
              ></div>
            </div>
            <div
              class="grid-view-rows"
              :style="{ transform: `translateY(${rowsTop}px)` }"
            >
              <!-- @TODO figure out a faster way to render the rows on scroll. -->
              <div
                v-for="row in rows"
                :key="'right-row-' + view.id + '-' + row.id"
                class="grid-view-row"
                :class="{
                  'grid-view-row-loading': row._.loading,
                  'grid-view-row-hover': row._.hover,
                }"
                @mouseover="setRowHover(row, true)"
                @mouseleave="setRowHover(row, false)"
                @contextmenu.prevent="showRowContext($event, row)"
              >
                <GridViewField
                  v-for="field in fields"
                  :ref="'row-' + row.id + '-field-' + field.id"
                  :key="
                    'right-row-field-' + view.id + '-' + row.id + '-' + field.id
                  "
                  :field="field"
                  :row="row"
                  :style="{ width: widths.fields[field.id] + 'px' }"
                  @selected="selectedField(field, $event.component)"
                  @selectPrevious="
                    selectNextField(row, field, fields, primary, 'previous')
                  "
                  @selectNext="selectNextField(row, field, fields, primary)"
                  @selectAbove="
                    selectNextField(row, field, fields, primary, 'above')
                  "
                  @selectBelow="
                    selectNextField(row, field, fields, primary, 'below')
                  "
                  @update="updateValue"
                ></GridViewField>
              </div>
            </div>
            <div class="grid-view-row">
              <div
                class="grid-view-column"
                :style="{ width: widths.rightFieldsOnly + 'px' }"
              >
                <a
                  class="grid-view-add-row"
                  :class="{ hover: addHover }"
                  @mouseover="addHover = true"
                  @mouseleave="addHover = false"
                  @click="addRow()"
                ></a>
              </div>
            </div>
          </div>
        </div>
        <div class="grid-view-foot"></div>
      </div>
    </div>
    <Context ref="rowContext">
      <ul class="context-menu">
        <li>
          <a @click="deleteRow(selectedRow)">
            <i class="context-menu-icon fas fa-fw fa-trash"></i>
            Delete row
          </a>
        </li>
      </ul>
    </Context>
    <RowEditModal
      ref="rowEditModal"
      :table="table"
      :primary="primary"
      :fields="fields"
      @update="updateValue"
    ></RowEditModal>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'

import CreateFieldContext from '@baserow/modules/database/components/field/CreateFieldContext'
import GridViewFieldType from '@baserow/modules/database/components/view/grid/GridViewFieldType'
import GridViewField from '@baserow/modules/database/components/view/grid/GridViewField'
import GridViewFieldWidthHandle from '@baserow/modules/database/components/view/grid/GridViewFieldWidthHandle'
import RowEditModal from '@baserow/modules/database/components/row/RowEditModal'
import { notifyIf } from '@baserow/modules/core/utils/error'
import _ from 'lodash'

export default {
  name: 'GridView',
  components: {
    CreateFieldContext,
    GridViewFieldType,
    GridViewField,
    GridViewFieldWidthHandle,
    RowEditModal,
  },
  props: {
    primary: {
      type: Object,
      required: true,
    },
    fields: {
      type: Array,
      required: true,
    },
    view: {
      type: Object,
      required: true,
    },
    table: {
      type: Object,
      required: true,
    },
    database: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      addHover: false,
      loading: true,
      selectedRow: null,
      lastHoveredRow: null,
      widths: {
        fields: {},
      },
    }
  },
  computed: {
    ...mapGetters({
      rows: 'view/grid/getRows',
      count: 'view/grid/getCount',
      rowHeight: 'view/grid/getRowHeight',
      rowsTop: 'view/grid/getRowsTop',
      placeholderHeight: 'view/grid/getPlaceholderHeight',
      fieldOptions: 'view/grid/getAllFieldOptions',
    }),
  },
  watch: {
    // The field options contain the widths of the field. Every time one of the values
    // changes we need to recalculate all the widths.
    fieldOptions: {
      deep: true,
      handler(value) {
        this.calculateWidths(this.primary, this.fields, value)
      },
    },
    // If a field is added or removed we need to recalculate all the widths.
    fields(value) {
      this.calculateWidths(this.primary, this.fields, this.fieldOptions)
    },
  },
  created() {
    // We have to calculate the widths when the component is created so that we can
    // render the page properly on the server side.
    this.calculateWidths(this.primary, this.fields, this.fieldOptions)
  },
  methods: {
    async updateValue({ field, row, value, oldValue }) {
      try {
        await this.$store.dispatch('view/grid/updateValue', {
          table: this.table,
          row,
          field,
          value,
          oldValue,
        })
      } catch (error) {
        notifyIf(error, 'field')
      }
    },
    scroll(pixelY, pixelX) {
      const $rightBody = this.$refs.rightBody
      const $right = this.$refs.right

      const top = $rightBody.scrollTop + pixelY
      const left = $right.scrollLeft + pixelX

      this.verticalScroll(top)
      this.horizontalScroll(left)

      this.$refs.scrollbars.update()
    },
    verticalScroll(top) {
      this.$refs.leftBody.scrollTop = top
      this.$refs.rightBody.scrollTop = top

      this.$store.dispatch('view/grid/fetchByScrollTopDelayed', {
        gridId: this.view.id,
        scrollTop: this.$refs.rightBody.scrollTop,
        windowHeight: this.$refs.rightBody.clientHeight,
      })
    },
    horizontalScroll(left) {
      const $right = this.$refs.right
      const $divider = this.$refs.divider
      const canScroll = $right.scrollWidth > $right.clientWidth

      $divider.classList.toggle('shadow', canScroll && left > 0)
      $right.scrollLeft = left
    },
    /**
     * Calculates the widths of all fields, left side, right side and place holder
     * positions and returns the values in an object.
     */
    getCalculatedWidths(primary, fields, fieldOptions) {
      const getFieldWidth = (fieldId) => {
        return Object.prototype.hasOwnProperty.call(fieldOptions, fieldId)
          ? fieldOptions[fieldId].width
          : 200
      }

      // Calculate the widths left side of the grid view. This is the sticky side that
      // contains the primary field and ids.
      const leftReserved = 60
      const leftFieldsOnly = getFieldWidth(primary.id)
      const left = leftFieldsOnly + leftReserved

      // Calculate the widths of the right side that contains all the other fields.
      const rightAdd = 100
      const rightReserved = 100
      const rightFieldsOnly = fields.reduce(
        (value, field) => getFieldWidth(field.id) + value,
        0
      )
      const right = rightFieldsOnly + rightAdd + rightReserved

      // Calculate the left positions of the placeholder columns. These are the gray
      // vertical lines that are always visible, even when the data hasn't loaded yet.
      let last = 0
      const placeholderPositions = {}
      fields.forEach((field) => {
        last += getFieldWidth(field.id)
        placeholderPositions[field.id] = last
      })

      const fieldWidths = {}
      fieldWidths[primary.id] = getFieldWidth(primary.id)
      fields.forEach((field) => {
        fieldWidths[field.id] = getFieldWidth(field.id)
      })

      return {
        left,
        leftReserved,
        leftFieldsOnly,
        right,
        rightReserved,
        rightAdd,
        rightFieldsOnly,
        placeholderPositions,
        fields: fieldWidths,
      }
    },
    /**
     * This method is called when the fieldOptions or fields changes. The reason why we
     * don't have smaller methods that are called from the template to calculate the
     * widths is that because that would quickly result in thousands of function calls
     * when the smallest things change in the data. This is a speed improving
     * workaround.
     */
    calculateWidths(primary, fields, fieldOptions) {
      _.assign(
        this.widths,
        this.getCalculatedWidths(primary, fields, fieldOptions)
      )

      if (this.$refs.scrollbars) {
        this.$refs.scrollbars.update()
      }
    },
    async addRow() {
      try {
        await this.$store.dispatch('view/grid/create', {
          table: this.table,
          // We need a list of all fields including the primary one here.
          fields: [this.primary].concat(...this.fields),
          values: {},
        })
      } catch (error) {
        notifyIf(error, 'row')
      }
    },
    showRowContext(event, row) {
      this.selectedRow = row
      this.$refs.rowContext.toggle(
        {
          top: event.clientY,
          left: event.clientX,
        },
        'bottom',
        'right',
        0
      )
    },
    async deleteRow(row) {
      try {
        this.$refs.rowContext.hide()
        // We need a small helper function that calculates the current scrollTop because
        // the delete action will recalculate the visible scroll range and buffer.
        const getScrollTop = () => this.$refs.leftBody.scrollTop
        await this.$store.dispatch('view/grid/delete', {
          table: this.table,
          grid: this.view,
          row,
          getScrollTop,
        })
      } catch (error) {
        notifyIf(error, 'row')
      }
    },
    /**
     * When a field is selected we want to make sure it is visible in the viewport, so
     * we might need to scroll a little bit.
     */
    selectedField(field, component) {
      const element = component.$el
      const verticalContainer = this.$refs.rightBody
      const horizontalContainer = this.$refs.right

      const verticalContainerRect = verticalContainer.getBoundingClientRect()
      const verticalContainerHeight = verticalContainer.clientHeight

      const horizontalContainerRect = horizontalContainer.getBoundingClientRect()
      const horizontalContainerWidth = horizontalContainer.clientWidth

      const elementRect = element.getBoundingClientRect()
      const elementTop = elementRect.top - verticalContainerRect.top
      const elementBottom = elementRect.bottom - verticalContainerRect.top
      const elementLeft = elementRect.left - horizontalContainerRect.left
      const elementRight = elementRect.right - horizontalContainerRect.left

      if (elementTop < 0) {
        // If the field isn't visible in the viewport we need to scroll up in order
        // to show it.
        this.verticalScroll(elementTop + verticalContainer.scrollTop - 20)
        this.$refs.scrollbars.updateVertical()
      } else if (elementBottom > verticalContainerHeight) {
        // If the field isn't visible in the viewport we need to scroll down in order
        // to show it.
        this.verticalScroll(
          elementBottom +
            verticalContainer.scrollTop -
            verticalContainer.clientHeight +
            20
        )
        this.$refs.scrollbars.updateVertical()
      }

      if (elementLeft < 0 && !field.primary) {
        // If the field isn't visible in the viewport we need to scroll left in order
        // to show it.
        this.horizontalScroll(elementLeft + horizontalContainer.scrollLeft - 20)
        this.$refs.scrollbars.updateHorizontal()
      } else if (elementRight > horizontalContainerWidth && !field.primary) {
        // If the field isn't visible in the viewport we need to scroll right in order
        // to show it.
        this.horizontalScroll(
          elementRight +
            horizontalContainer.scrollLeft -
            horizontalContainer.clientWidth +
            20
        )
        this.$refs.scrollbars.updateHorizontal()
      }
    },
    /**
     * This method is called when the next field must be selected. This can for example
     * happen when the tab key is pressed. It tries to find the next field and will
     * select that one.
     */
    selectNextField(row, field, fields, primary, direction = 'next') {
      let nextFieldId = -1
      let nextRowId = -1

      if (direction === 'next' || direction === 'previous') {
        nextRowId = row.id

        if (field.primary && fields.length > 0 && direction === 'next') {
          // If the currently selected field is the primary we can just select the
          // first field of the fields if there are any.
          nextFieldId = fields[0].id
        } else if (!field.primary) {
          // First we need to know which index the currently selected field has in the
          // fields list.
          const index = fields.findIndex((f) => f.id === field.id)
          if (direction === 'next' && fields.length > index + 1) {
            // If we want to select the next field we can just check if the next index
            // exists and read the id from there.
            nextFieldId = fields[index + 1].id
          } else if (direction === 'previous' && index > 0) {
            // If we want to select the previous field we can just check if aren't
            // already the first and read the id from the previous.
            nextFieldId = fields[index - 1].id
          } else if (direction === 'previous' && index === 0) {
            // If we want to select the previous field and we already are the first
            // index we just select the primary.
            nextFieldId = primary.id
          }
        }
      }

      if (direction === 'below' || direction === 'above') {
        nextFieldId = field.id
        const rows = this.$store.getters['view/grid/getAllRows']
        const index = rows.findIndex((r) => r.id === row.id)

        if (index !== -1 && direction === 'below' && rows.length > index + 1) {
          // If the next row index exists we can select the same field in the next row.
          nextRowId = rows[index + 1].id
        } else if (index !== -1 && direction === 'above' && index > 0) {
          // If the previous row index exists we can select the same field in the
          // previous row.
          nextRowId = rows[index - 1].id
        }
      }

      if (nextFieldId === -1 || nextRowId === -1) {
        return
      }

      const current = this.$refs['row-' + row.id + '-field-' + field.id]
      const next = this.$refs['row-' + nextRowId + '-field-' + nextFieldId]

      if (next === undefined || current === undefined) {
        return
      }

      current[0].unselect()
      next[0].select()
    },
    setRowHover(row, value) {
      // Sometimes the mouseleave is not triggered, but because you can hover only one
      // row at a time we can remember which was hovered last and set the hover state to
      // false if it differs.
      if (this.lastHoveredRow !== null && this.lastHoveredRow.id !== row.id) {
        this.$store.dispatch('view/grid/setRowHover', {
          row: this.lastHoveredRow,
          value: false,
        })
        this.lastHoveredRow = true
      }

      this.$store.dispatch('view/grid/setRowHover', { row, value })
      this.lastHoveredRow = row
    },
  },
}
</script>
