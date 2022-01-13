<template>
  <div>
    <div class="grid-view__inner" :style="{ 'min-width': width + 'px' }">
      <GridViewHead
        :table="table"
        :view="view"
        :fields="fields"
        :include-field-width-handles="includeFieldWidthHandles"
        :include-row-details="includeRowDetails"
        :include-add-field="includeAddField"
        :read-only="readOnly"
        :store-prefix="storePrefix"
        @refresh="$emit('refresh', $event)"
        @dragging="
          canOrderFields &&
            $refs.fieldDragging.start($event.field, $event.event)
        "
      ></GridViewHead>
      <div ref="body" class="grid-view__body">
        <div class="grid-view__body-inner">
          <GridViewPlaceholder
            :fields="fields"
            :include-row-details="includeRowDetails"
            :store-prefix="storePrefix"
          ></GridViewPlaceholder>
          <GridViewRows
            ref="rows"
            :table="table"
            :view="view"
            :fields="fieldsToRender"
            :left-offset="fieldsLeftOffset"
            :include-row-details="includeRowDetails"
            :read-only="readOnly"
            :store-prefix="storePrefix"
            v-on="$listeners"
          ></GridViewRows>
          <GridViewRowAdd
            v-if="!readOnly"
            :fields="fields"
            :include-row-details="includeRowDetails"
            :store-prefix="storePrefix"
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
      :fields="fields"
      :container-width="width"
      :read-only="readOnly"
      :store-prefix="storePrefix"
      @scroll="$emit('scroll', $event)"
    ></GridViewFieldDragging>
  </div>
</template>

<script>
import debounce from 'lodash/debounce'
import ResizeObserver from 'resize-observer-polyfill'

import GridViewHead from '@baserow/modules/database/components/view/grid/GridViewHead'
import GridViewPlaceholder from '@baserow/modules/database/components/view/grid/GridViewPlaceholder'
import GridViewRows from '@baserow/modules/database/components/view/grid/GridViewRows'
import GridViewRowAdd from '@baserow/modules/database/components/view/grid/GridViewRowAdd'
import GridViewFieldDragging from '@baserow/modules/database/components/view/grid/GridViewFieldDragging'
import gridViewHelpers from '@baserow/modules/database/mixins/gridViewHelpers'

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
    readOnly: {
      type: Boolean,
      required: true,
    },
  },
  data() {
    return {
      // Render the first 20 fields by default so that there's at least some data when
      // the page is server side rendered.
      fieldsToRender: this.fields.slice(0, 20),
      // Indicates the offset
      fieldsLeftOffset: 0,
    }
  },
  computed: {
    /**
     * Calculates the total width of the whole section based on the fields and the
     * given options.
     */
    width() {
      let width = Object.values(this.fields).reduce(
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
  watch: {
    fieldOptions: {
      deep: true,
      handler() {
        this.updateVisibleFieldsInRow()
      },
    },
    fields: {
      deep: true,
      handler() {
        this.updateVisibleFieldsInRow()
      },
    },
  },
  mounted() {
    // When the component first loads, we need to check
    this.updateVisibleFieldsInRow()

    const updateDebounced = debounce(() => {
      this.updateVisibleFieldsInRow()
    }, 50)

    // When the viewport resizes, we need to check if there are fields that must be
    // rendered.
    this.$el.resizeObserver = new ResizeObserver(() => {
      updateDebounced()
    })
    this.$el.resizeObserver.observe(this.$el)

    // When the user scrolls horizontally, we need to check if there fields/cells that
    // have moved into the viewport and must be rendered.
    const fireUpdateBuffer = {
      last: Date.now(),
      distance: 0,
    }
    this.$el.horizontalScrollEvent = (event) => {
      // Call the update order debounce function to simulate a stop scrolling event.
      updateDebounced()

      const now = Date.now()
      const { scrollLeft } = event.target

      const distance = Math.abs(scrollLeft - fireUpdateBuffer.distance)
      const timeDelta = now - fireUpdateBuffer.last

      if (timeDelta > 100) {
        const velocity = distance / timeDelta

        fireUpdateBuffer.last = now
        fireUpdateBuffer.distance = scrollLeft

        if (velocity < 2.5) {
          updateDebounced.cancel()
          this.updateVisibleFieldsInRow()
        }
      }
    }
    this.$el.addEventListener('scroll', this.$el.horizontalScrollEvent)
  },
  beforeDestroy() {
    this.$el.resizeObserver.unobserve(this.$el)
    this.$el.removeEventListener('scroll', this.$el.horizontalScrollEvent)
  },
  methods: {
    /**
     * For performance reasons we only want to render the cells are visible in the
     * viewport. This method makes sure that the right cells/fields are visible. It's
     * for example called when the user scrolls, when the window is resized or when a
     * field changes.
     */
    updateVisibleFieldsInRow() {
      const width = this.$el.clientWidth
      const scrollLeft = this.$el.scrollLeft
      // The padding is added to the start and end of the viewport to make sure that
      // cells nearby will always be ready to be displayed.
      const padding = 200
      const viewportStart = scrollLeft - padding
      const viewportEnd = scrollLeft + width + padding
      let leftOffset = null
      let left = 0

      // Create an array containing the fields that are currently visible in the
      // viewport and must be rendered.
      const fieldsToRender = this.fields.filter((field) => {
        const width = this.getFieldWidth(field.id)
        const right = left + width
        const visible = right >= viewportStart && left <= viewportEnd
        if (visible && leftOffset === null) {
          leftOffset = left
        }
        left = right
        return visible
      })

      if (
        JSON.stringify(this.fieldsToRender) !== JSON.stringify(fieldsToRender)
      ) {
        this.fieldsToRender = fieldsToRender
      }

      if (leftOffset !== this.fieldsLeftOffset) {
        this.fieldsLeftOffset = leftOffset
      }
    },
  },
}
</script>
