<template>
  <div v-scroll="scroll" class="grid-view">
    <Scrollbars
      ref="scrollbars"
      horizontal="getHorizontalScrollbarElement"
      vertical="getVerticalScrollbarElement"
      :style="{ left: leftWidth + 'px' }"
      @vertical="verticalScroll"
      @horizontal="horizontalScroll"
    ></Scrollbars>
    <GridViewSection
      ref="left"
      class="grid-view__left"
      :fields="leftFields"
      :table="table"
      :view="view"
      :include-field-width-handles="false"
      :include-row-details="true"
      :read-only="readOnly"
      :store-prefix="storePrefix"
      :style="{ width: leftWidth + 'px' }"
      @refresh="$emit('refresh', $event)"
      @row-hover="setRowHover($event.row, $event.value)"
      @row-context="showRowContext($event.event, $event.row)"
      @row-dragging="rowDragStart"
      @add-row="addRow()"
      @update="updateValue"
      @edit="editValue"
      @selected="selectedCell($event)"
      @unselected="unselectedCell($event)"
      @select-next="selectNextCell($event)"
      @edit-modal="$refs.rowEditModal.show($event.id)"
    >
      <template #foot>
        <div class="grid-view__column" :style="{ width: leftWidth + 'px' }">
          <div class="grid-view__foot-info">
            {{ $tc('gridView.rowCount', count, { count }) }}
          </div>
        </div>
      </template>
    </GridViewSection>
    <div
      ref="divider"
      class="grid-view__divider"
      :style="{ left: leftWidth + 'px' }"
    ></div>
    <GridViewFieldWidthHandle
      class="grid-view__divider-width"
      :style="{ left: leftWidth + 'px' }"
      :grid="view"
      :field="primary"
      :width="leftFieldsWidth"
      :store-prefix="storePrefix"
    ></GridViewFieldWidthHandle>
    <GridViewSection
      ref="right"
      class="grid-view__right"
      :fields="visibleFields"
      :table="table"
      :view="view"
      :include-add-field="true"
      :can-order-fields="true"
      :read-only="readOnly"
      :store-prefix="storePrefix"
      :style="{ left: leftWidth + 'px' }"
      @refresh="$emit('refresh', $event)"
      @row-hover="setRowHover($event.row, $event.value)"
      @row-context="showRowContext($event.event, $event.row)"
      @add-row="addRow()"
      @update="updateValue"
      @edit="editValue"
      @selected="selectedCell($event)"
      @unselected="unselectedCell($event)"
      @select-next="selectNextCell($event)"
      @edit-modal="$refs.rowEditModal.show($event.id)"
      @scroll="scroll($event.pixelY, $event.pixelX)"
    ></GridViewSection>
    <GridViewRowDragging
      ref="rowDragging"
      :table="table"
      :view="view"
      :primary="primary"
      :fields="visibleFields"
      :store-prefix="storePrefix"
      vertical="getVerticalScrollbarElement"
      @scroll="scroll($event.pixelY, $event.pixelX)"
    ></GridViewRowDragging>
    <Context ref="rowContext">
      <ul class="context__menu">
        <li v-if="!readOnly">
          <a @click=";[addRow(selectedRow), $refs.rowContext.hide()]">
            <i class="context__menu-icon fas fa-fw fa-arrow-up"></i>
            {{ $t('gridView.insertRowAbove') }}
          </a>
        </li>
        <li v-if="!readOnly">
          <a @click=";[addRowAfter(selectedRow), $refs.rowContext.hide()]">
            <i class="context__menu-icon fas fa-fw fa-arrow-down"></i>
            {{ $t('gridView.insertRowBelow') }}
          </a>
        </li>
        <li>
          <a
            @click="
              ;[
                $refs.rowEditModal.show(selectedRow.id),
                $refs.rowContext.hide(),
              ]
            "
          >
            <i class="context__menu-icon fas fa-fw fa-expand"></i>
            {{ $t('gridView.enlargeRow') }}
          </a>
        </li>
        <li v-if="!readOnly">
          <a @click="deleteRow(selectedRow)">
            <i class="context__menu-icon fas fa-fw fa-trash"></i>
            {{ $t('gridView.deleteRow') }}
          </a>
        </li>
      </ul>
    </Context>
    <RowEditModal
      ref="rowEditModal"
      :table="table"
      :primary="primary"
      :fields="fields"
      :rows="allRows"
      :read-only="readOnly"
      @refresh="$emit('refresh', $event)"
      @update="updateValue"
      @hidden="rowEditModalHidden"
      @field-updated="$emit('refresh', $event)"
      @field-deleted="$emit('refresh')"
    ></RowEditModal>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'

import { notifyIf } from '@baserow/modules/core/utils/error'
import GridViewSection from '@baserow/modules/database/components/view/grid/GridViewSection'
import GridViewFieldWidthHandle from '@baserow/modules/database/components/view/grid/GridViewFieldWidthHandle'
import GridViewRowDragging from '@baserow/modules/database/components/view/grid/GridViewRowDragging'
import RowEditModal from '@baserow/modules/database/components/row/RowEditModal'
import gridViewHelpers from '@baserow/modules/database/mixins/gridViewHelpers'
import { maxPossibleOrderValue } from '@baserow/modules/database/viewTypes'

export default {
  name: 'GridView',
  components: {
    GridViewSection,
    GridViewFieldWidthHandle,
    GridViewRowDragging,
    RowEditModal,
  },
  mixins: [gridViewHelpers],
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
    readOnly: {
      type: Boolean,
      required: true,
    },
  },
  data() {
    return {
      lastHoveredRow: null,
      selectedRow: null,
    }
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
            : maxPossibleOrderValue
          const orderB = this.fieldOptions[b.id]
            ? this.fieldOptions[b.id].order
            : maxPossibleOrderValue

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
    leftFields() {
      return [this.primary]
    },
    leftFieldsWidth() {
      return this.leftFields.reduce(
        (value, field) => this.getFieldWidth(field.id) + value,
        0
      )
    },
    leftWidth() {
      return this.leftFieldsWidth + this.gridViewRowDetailsWidth
    },
  },
  watch: {
    fieldOptions: {
      deep: true,
      handler() {
        // When the field options have changed, it could be that the width of the
        // fields have changed and in that case we want to update the scrollbars.
        this.fieldsUpdated()
      },
    },
    fields() {
      // When a field is added or removed, we want to update the scrollbars.
      this.fieldsUpdated()
    },
  },
  beforeCreate() {
    this.$options.computed = {
      ...(this.$options.computed || {}),
      ...mapGetters({
        allRows: this.$options.propsData.storePrefix + 'view/grid/getAllRows',
        count: this.$options.propsData.storePrefix + 'view/grid/getCount',
      }),
    }
  },
  created() {
    // When the grid view is created we want to update the scrollbars.
    this.fieldsUpdated()
  },
  beforeMount() {
    this.$bus.$on('field-deleted', this.fieldDeleted)
  },
  mounted() {
    this.$el.resizeEvent = () => {
      const height = this.$refs.left.$refs.body.clientHeight
      this.$store.dispatch(
        this.storePrefix + 'view/grid/setWindowHeight',
        height
      )
    }
    this.$el.resizeEvent()
    window.addEventListener('resize', this.$el.resizeEvent)
  },
  beforeDestroy() {
    window.removeEventListener('resize', this.$el.resizeEvent)
    this.$bus.$off('field-deleted', this.fieldDeleted)
  },
  methods: {
    /**
     * When a field is deleted we need to check if that field was related to any
     * filters or sortings. If that is the case then the view needs to be refreshed so
     * we can see fresh results.
     */
    fieldDeleted({ field }) {
      const filterIndex = this.view.filters.findIndex((filter) => {
        return filter.field === field.id
      })
      const sortIndex = this.view.sortings.findIndex((sort) => {
        return sort.field === field.id
      })
      if (filterIndex > -1 || sortIndex > -1) {
        this.$emit('refresh')
      }
    },
    /**
     * Is called when anything related to a field has changed and in that case we want
     * to update the scrollbars.
     */
    fieldsUpdated() {
      const scrollbars = this.$refs.scrollbars
      // Vue can sometimes trigger this via watch before the child component
      // scrollbars has been created, check it exists and has the expected method
      if (scrollbars && scrollbars.update) {
        scrollbars.update()
      }
    },
    /**
     * Called when a cell value has been updated. This can for example happen via the
     * row edit modal or when editing a cell directly in the grid.
     */
    async updateValue({ field, row, value, oldValue }) {
      try {
        await this.$store.dispatch(
          this.storePrefix + 'view/grid/updateRowValue',
          {
            table: this.table,
            view: this.view,
            fields: this.fields,
            primary: this.primary,
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
     * Called when a value is edited, but not yet saved. Here we can do a preliminary
     * check to see if the values matches the filters.
     */
    editValue({ field, row, value, oldValue }) {
      const overrides = {}
      overrides[`field_${field.id}`] = value
      this.$store.dispatch(this.storePrefix + 'view/grid/onRowChange', {
        view: this.view,
        row,
        fields: this.fields,
        primary: this.primary,
        overrides,
      })
    },
    /**
     * This method is called by the Scrollbars component and should return the element
     * that handles the the horizontal scrolling.
     */
    getHorizontalScrollbarElement() {
      return this.$refs.right.$el
    },
    /**
     * This method is called by the Scrollbars component and should return the element
     * that handles the the vertical scrolling.
     */
    getVerticalScrollbarElement() {
      return this.$refs.right.$refs.body
    },
    /**
     * Called when a user scrolls without using the scrollbar.
     */
    scroll(pixelY, pixelX) {
      const $rightBody = this.$refs.right.$refs.body
      const $right = this.$refs.right.$el

      const top = $rightBody.scrollTop + pixelY
      const left = $right.scrollLeft + pixelX

      this.verticalScroll(top)
      this.horizontalScroll(left)

      this.$refs.scrollbars.update()
    },
    /**
     * Called when the user scrolls vertically. The scroll offset of both the left and
     * right section must be updated and we want might need to fetch new rows which
     * is handled by the grid view store.
     */
    verticalScroll(top) {
      this.$refs.left.$refs.body.scrollTop = top
      this.$refs.right.$refs.body.scrollTop = top

      this.$store.dispatch(
        this.storePrefix + 'view/grid/fetchByScrollTopDelayed',
        {
          scrollTop: this.$refs.left.$refs.body.scrollTop,
          fields: this.fields,
          primary: this.primary,
        }
      )
    },
    /**
     * Called when the user scrolls horizontally. If the user scrolls we might want to
     * show a shadow next to the left section because that one has a fixed position.
     */
    horizontalScroll(left) {
      const $right = this.$refs.right.$el
      const $divider = this.$refs.divider
      const canScroll = $right.scrollWidth > $right.clientWidth

      $divider.classList.toggle('shadow', canScroll && left > 0)
      $right.scrollLeft = left
    },
    async addRow(before = null) {
      try {
        await this.$store.dispatch(
          this.storePrefix + 'view/grid/createNewRow',
          {
            view: this.view,
            table: this.table,
            // We need a list of all fields including the primary one here.
            fields: this.fields,
            primary: this.primary,
            values: {},
            before,
          }
        )
      } catch (error) {
        notifyIf(error, 'row')
      }
    },
    /**
     * Because it is only possible to add a new row before another row, we have to
     * figure out which row is below the given row and insert before that one. If the
     * next row is not found, we can safely assume it is the last row and add it last.
     */
    addRowAfter(row) {
      const rows =
        this.$store.getters[this.storePrefix + 'view/grid/getAllRows']
      const index = rows.findIndex((r) => r.id === row.id)
      let nextRow = null

      if (index !== -1 && rows.length > index + 1) {
        nextRow = rows[index + 1]
      }

      this.addRow(nextRow)
    },
    async deleteRow(row) {
      try {
        this.$refs.rowContext.hide()
        // We need a small helper function that calculates the current scrollTop because
        // the delete action will recalculate the visible scroll range and buffer.
        const getScrollTop = () => this.$refs.left.$refs.body.scrollTop
        await this.$store.dispatch(
          this.storePrefix + 'view/grid/deleteExistingRow',
          {
            table: this.table,
            view: this.view,
            fields: this.fields,
            primary: this.primary,
            row,
            getScrollTop,
          }
        )
        await this.$store.dispatch('notification/restore', {
          trash_item_type: 'row',
          parent_trash_item_id: this.table.id,
          trash_item_id: row.id,
        })
      } catch (error) {
        notifyIf(error, 'row')
      }
    },
    setRowHover(row, value) {
      // Sometimes the mouseleave is not triggered, but because you can hover only one
      // row at a time we can remember which was hovered last and set the hover state to
      // false if it differs.
      if (this.lastHoveredRow !== null && this.lastHoveredRow.id !== row.id) {
        this.$store.dispatch(this.storePrefix + 'view/grid/setRowHover', {
          row: this.lastHoveredRow,
          value: false,
        })
        this.lastHoveredRow = null
      }

      this.$store.dispatch(this.storePrefix + 'view/grid/setRowHover', {
        row,
        value,
      })
      this.lastHoveredRow = row
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
    /**
     * Called when the user starts dragging the row. This will initiate the dragging
     * effect and allows the user to move it to another position.
     */
    rowDragStart({ event, row }) {
      this.$refs.rowDragging.start(row, event)
    },
    /**
     * When the modal hides and the related row does not match the filters anymore it
     * must be deleted.
     */
    rowEditModalHidden({ row }) {
      // It could be that the row is not in the buffer anymore and in that case we also
      // don't need to refresh the row.
      if (
        row === undefined ||
        !Object.prototype.hasOwnProperty.call(row, 'id')
      ) {
        return
      }

      this.$store.dispatch(this.storePrefix + 'view/grid/refreshRow', {
        grid: this.view,
        fields: this.fields,
        primary: this.primary,
        row,
        getScrollTop: () => this.$refs.left.$refs.body.scrollTop,
      })
    },
    /**
     * When a cell is selected we want to make sure it is visible in the viewport, so
     * we might need to scroll a little bit.
     */
    selectedCell({ component, row, field }) {
      const element = component.$el
      const verticalContainer = this.$refs.right.$refs.body
      const horizontalContainer = this.$refs.right.$el

      const verticalContainerRect = verticalContainer.getBoundingClientRect()
      const verticalContainerHeight = verticalContainer.clientHeight

      const horizontalContainerRect =
        horizontalContainer.getBoundingClientRect()
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

      this.$store.dispatch(this.storePrefix + 'view/grid/addRowSelectedBy', {
        row,
        field,
      })
    },
    /**
     * When a cell is unselected need to change the selected state of the row.
     */
    unselectedCell({ row, field }) {
      // We want to change selected state of the row on the next tick because if another
      // cell within a row is selected, we want to wait for that selected state tot
      // change. This will make sure that the row is stays selected.
      this.$nextTick(() => {
        // The getScrollTop function tries to find the vertically scrollable element
        // and returns the scrollTop value. The unselectCell method could in some cases
        // be called when the grid view component has already been destroyed. For
        // example when a cell is selected in the template modal and the user presses
        // the escape key which destroys the modal. We need to make sure, the lookup
        // doesn't fail hard when that happens, so we can return the last scroll top
        // value stored in the grid view store.
        let getScrollTop = () => this.$refs.left.$refs.body.scrollTop
        if (!this.$refs.left) {
          getScrollTop = () =>
            this.$store.getters[this.storePrefix + 'view/grid/getScrollTop']
        }
        this.$store.dispatch(
          this.storePrefix + 'view/grid/removeRowSelectedBy',
          {
            grid: this.view,
            fields: this.fields,
            primary: this.primary,
            row,
            field,
            getScrollTop,
          }
        )
      })
    },
    /**
     * This method is called when the next cell must be selected. This can for example
     * happen when the tab key is pressed. It tries to find the next field based on the
     * direction and will select that one.
     */
    selectNextCell({ row, field, direction = 'next' }) {
      const fields = this.visibleFields
      const primary = this.primary
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
        const rows =
          this.$store.getters[this.storePrefix + 'view/grid/getAllRows']
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

      this.$store.dispatch(this.storePrefix + 'view/grid/setSelectedCell', {
        rowId: nextRowId,
        fieldId: nextFieldId,
      })
    },
    /**
     * This method is called from the parent component when the data in the view has
     * been reset. This can for example happen when a user creates or updates a filter
     * or wants to sort on a field.
     */
    async refresh() {
      await this.$store.dispatch(
        this.storePrefix + 'view/grid/visibleByScrollTop',
        this.$refs.right.$refs.body.scrollTop
      )
      this.$nextTick(() => {
        this.fieldsUpdated()
      })
    },
  },
}
</script>

<i18n>
{
  "en": {
    "gridView":{
      "insertRowAbove": "Insert row above",
      "insertRowBelow": "Insert row below",
      "enlargeRow": "Enlarge row",
      "deleteRow": "Delete row",
      "rowCount": "No rows | 1 row | {count} rows"
    }
  },  
  "fr": {
    "gridView":{
      "insertRowAbove": "Insérer au dessus",
      "insertRowBelow": "Insérer en dessous",
      "enlargeRow": "Afficher la ligne",
      "deleteRow": "Supprimer la ligne",
      "rowCount": "Acunne ligne | 1 ligne | {count} lignes"
    }
  }
}
</i18n>
