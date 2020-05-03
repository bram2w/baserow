<template>
  <div v-scroll="scroll" class="grid-view">
    <Scrollbars
      ref="scrollbars"
      horizontal="right"
      vertical="rightBody"
      :style="{ left: getLeftWidth() + 'px' }"
      @vertical="verticalScroll"
      @horizontal="horizontalScroll"
    ></Scrollbars>
    <div class="grid-view-left" :style="{ width: getLeftWidth() + 'px' }">
      <div class="grid-view-inner" :style="{ width: getLeftWidth() + 'px' }">
        <div class="grid-view-head">
          <div class="grid-view-column" style="width: 60px;"></div>
          <GridViewFieldType
            v-if="primary !== null"
            :field="primary"
          ></GridViewFieldType>
        </div>
        <div ref="leftBody" class="grid-view-body">
          <div class="grid-view-body-inner">
            <div
              class="grid-view-placeholder"
              style="width: 260px;"
              :style="{ height: placeholderHeight + 'px' }"
            >
              <div
                class="grid-view-placeholder-column"
                style="width: 260px;"
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
                :class="{ 'grid-view-row-loading': row._.loading }"
                @contextmenu.prevent="showRowContext($event, row)"
              >
                <div class="grid-view-column" style="width: 60px;">
                  <div class="grid-view-row-info">
                    <div class="grid-view-row-count">{{ row.id }}</div>
                    <a href="#" class="grid-view-row-more">
                      <i class="fas fa-expand"></i>
                    </a>
                  </div>
                </div>
                <GridViewField
                  v-if="primary !== null"
                  :ref="'row-' + row.id + '-field-' + primary.id"
                  :field="primary"
                  :row="row"
                  :table="table"
                  @selected="selectedField(primary, $event.component)"
                  @selectNext="selectNextField(row, primary, fields, primary)"
                ></GridViewField>
              </div>
            </div>
            <div class="grid-view-row">
              <div
                class="grid-view-column"
                :style="{ width: getLeftWidth() + 'px' }"
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
          <div
            class="grid-view-column"
            :style="{ width: getLeftWidth() + 'px' }"
          >
            <div class="grid-view-foot-info">{{ count }} rows</div>
          </div>
        </div>
      </div>
    </div>
    <div
      ref="divider"
      class="grid-view-divider"
      :style="{ left: getLeftWidth() + 'px' }"
    ></div>
    <div
      ref="right"
      class="grid-view-right"
      :style="{ left: getLeftWidth() + 'px' }"
    >
      <div
        class="grid-view-inner"
        :style="{ 'min-width': getRightWidth() + 'px' }"
      >
        <div class="grid-view-head">
          <GridViewFieldType
            v-for="field in fields"
            :key="'right-head-field-' + view.id + '-' + field.id"
            :field="field"
          ></GridViewFieldType>
          <div class="grid-view-column" style="width: 100px;">
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
                width: fields.length * 200 + 'px',
              }"
            >
              <div
                v-for="(field, index) in fields"
                :key="'right-placeholder-column-' + view.id + '-' + field.id"
                class="grid-view-placeholder-column"
                :style="{ left: (index + 1) * 200 - 1 + 'px' }"
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
                :class="{ 'grid-view-row-loading': row._.loading }"
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
                  :table="table"
                  @selected="selectedField(field, $event.component)"
                  @selectPrevious="
                    selectNextField(row, field, fields, primary, true)
                  "
                  @selectNext="selectNextField(row, field, fields, primary)"
                ></GridViewField>
              </div>
            </div>
            <div class="grid-view-row">
              <div
                class="grid-view-column"
                :style="{ width: getRightWidth(true) + 'px' }"
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
  </div>
</template>

<script>
import { mapGetters } from 'vuex'

import CreateFieldContext from '@baserow/modules/database/components/field/CreateFieldContext'
import GridViewFieldType from '@baserow/modules/database/components/view/grid/GridViewFieldType'
import GridViewField from '@baserow/modules/database/components/view/grid/GridViewField'
import { notifyIf } from '@baserow/modules/core/utils/error'

export default {
  name: 'GridView',
  components: {
    CreateFieldContext,
    GridViewFieldType,
    GridViewField,
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
    }
  },
  computed: {
    ...mapGetters({
      rows: 'view/grid/getRows',
      count: 'view/grid/getCount',
      rowHeight: 'view/grid/getRowHeight',
      rowsTop: 'view/grid/getRowsTop',
      placeholderHeight: 'view/grid/getPlaceholderHeight',
    }),
  },
  methods: {
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
    getLeftWidth() {
      const space = 60
      const left = 1 * 200
      return space + left
    },
    getRightWidth(columnsOnly = false) {
      const right = this.fields.length * 200
      const add = 100
      const space = 100
      return right + (columnsOnly ? 0 : add + space)
    },
    async addRow() {
      try {
        await this.$store.dispatch('view/grid/create', {
          table: this.table,
          fields: this.fields,
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
     * When a field is selected we want to make sure it is visible so we might need to
     * scroll a little bit. Because the primary fields are always visible we don't have
     * to do anything when those are selected.
     */
    selectedField(field, component) {
      if (field.primary) {
        return
      }

      const container = this.$refs.right
      const containerLeft = container.scrollLeft
      const containerWidth = container.clientWidth
      const containerRight = containerLeft + container.clientWidth

      const element = component.$el
      const elementLeft = element.offsetLeft
      const elementWidth = element.offsetWidth
      const elementRight = element.offsetLeft + element.offsetWidth

      if (elementWidth >= containerWidth || elementLeft < containerLeft) {
        // If the element doesn't fit in the viewport we just want to make sure the
        // beginning is visible.
        container.scrollLeft = elementLeft - 20
        this.$refs.scrollbars.updateHorizontal()
      } else if (elementRight > containerRight) {
        // If the right side if the element isn't visible within the viewport.
        // The +10 is a small padding.
        container.scrollLeft = elementRight - containerWidth + 20
        this.$refs.scrollbars.updateHorizontal()
      }
    },
    /**
     * This method is called when the next field must be selected. This can for example
     * happen when the tab key is pressed. It tries to find the next field and will
     * select that one.
     */
    selectNextField(row, field, fields, primary, previous = false) {
      let nextFieldId = -1
      if (field.primary && fields.length > 0 && !previous) {
        // If the currently selected field is the primary we can just select the first
        // field of the fields if there are any.
        nextFieldId = fields[0].id
      } else if (!field.primary) {
        // First we need to know which index the currently selected field has in the
        // fields list.
        const index = fields.findIndex((f) => f.id === field.id)
        if (!previous && fields.length > index + 1) {
          // If we want to select the next field we can just check if the next index
          // exists and read the id from there.
          nextFieldId = fields[index + 1].id
        } else if (previous && index > 0) {
          // If we want to select the previous field we can just check if aren't already
          // the first and read the id from the previous.
          nextFieldId = fields[index - 1].id
        } else if (previous && index === 0) {
          // If we want to select the previous field and we already are the first index
          // we just select the primary.
          nextFieldId = primary.id
        }
      }

      if (nextFieldId === -1) {
        return
      }

      const current = this.$refs['row-' + row.id + '-field-' + field.id]
      const next = this.$refs['row-' + row.id + '-field-' + nextFieldId]

      if (next.length === 0 || current.length === 0) {
        return
      }

      current[0].unselect()
      next[0].select()
    },
  },
}
</script>
