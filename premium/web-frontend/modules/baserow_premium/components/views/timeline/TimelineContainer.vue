<template>
  <div class="timeline-container">
    <div class="timeline-container__header">
      <ViewDateIndicator
        v-if="firstVisibleDate"
        :selected-date="firstVisibleDate"
      />
      <ViewDateSelector
        v-if="firstVisibleDate"
        :selected-date="firstVisibleDate"
        :unit="timescale"
        @date-selected="scrollDateIntoView"
      />
    </div>
    <div ref="gridHeader" class="timeline-container__grid-header">
      <TimelineGridHeader
        v-if="gridReady"
        :columns-buffer="columnsBuffer"
        :column-count="columns.length"
        :column-width="columnWidth"
      />
    </div>
    <div ref="gridBody" class="timeline-container__grid-body">
      <TimelineGrid
        v-if="gridReady"
        :columns-buffer="columnsBuffer"
        :column-width="columnWidth"
        :column-count="columns.length"
        :min-height="gridHeight"
      />
    </div>
  </div>
</template>
<script>
import { mapGetters } from 'vuex'
import ResizeObserver from 'resize-observer-polyfill'
import debounce from 'lodash/debounce'
import moment from '@baserow/modules/core/moment'
import {
  recycleSlots,
  orderSlots,
} from '@baserow/modules/database/utils/virtualScrolling'
import ViewDateIndicator from '@baserow_premium/components/views/ViewDateIndicator'
import ViewDateSelector from '@baserow_premium/components/views/ViewDateSelector'
import TimelineGridHeader from '@baserow_premium/components/views/timeline/TimelineGridHeader'
import TimelineGrid from '@baserow_premium/components/views/timeline/TimelineGrid'
import viewHelpers from '@baserow/modules/database/mixins/viewHelpers'
import timelineViewHelpers from '@baserow_premium/mixins/timelineViewHelpers'

export default {
  name: 'TimelineContainer',
  components: {
    TimelineGridHeader,
    TimelineGrid,
    ViewDateIndicator,
    ViewDateSelector,
  },
  mixins: [viewHelpers, timelineViewHelpers],
  props: {
    view: {
      type: Object,
      required: true,
    },
    fields: {
      type: Array,
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
    storePrefix: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      minColumnWidth: 32,
      columnWidth: null,
      columnsBuffer: [],
      columns: [],
      prevScrollLeft: null,
      gridWidth: null,
      gridHeight: null,
      firstVisibleDate: null,
      // timescale settings
      unit: null,
      timescale: null,
      visibleColumnCount: null,
      firstAvailableDate: null,
      lastAvailableDate: null,
    }
  },
  computed: {
    scrollAreaElement() {
      return this.$refs.gridBody
    },
    gridBodyHeightOffset() {
      return this.viewHeaderHeight + this.gridHeaderHeight
    },
    gridReady() {
      return this.columnWidth !== null
    },
    activeSearchTerm() {
      return this.$store.getters[
        `${this.storePrefix}view/timeline/getActiveSearchTerm`
      ]
    },
  },
  mounted() {
    // Sets the initial grid dimensions and initializes the grid columns
    // with dates based on the timescale settings.
    this.initTimescale()
    this.initGridColumns()

    // Setup the scroll event listener to update the grid when the user scrolls.
    const setupGridDebounced = debounce(this.onResizeUpdateGridColumns, 100)
    const onScroll = () => {
      const el = this.scrollAreaElement

      // horizontal scrolling
      if (el.scrollLeft !== this.prevScrollLeft) {
        this.onHorizontalScrollUpdateGridColumns()
        this.$refs.gridHeader.scroll({ left: el.scrollLeft })
      }
    }

    const el = this.scrollAreaElement
    el.addEventListener('scroll', onScroll)
    this.$once('hook:beforeDestroy', () => {
      el.removeEventListener('scroll', onScroll)
    })

    // Setup the resize observer to update the grid when the size of the container changes.
    const resizeObserver = new ResizeObserver(() => {
      setupGridDebounced()
    })
    resizeObserver.observe(el)
    this.$once('hook:beforeDestroy', () => {
      resizeObserver.unobserve(el)
    })
  },
  beforeCreate() {
    this.$options.computed = {
      ...(this.$options.computed || {}),
      ...mapGetters({
        fieldOptions:
          this.$options.propsData.storePrefix +
          'view/timeline/getAllFieldOptions',
      }),
    }
  },
  methods: {
    /*
     * Initializes the timescale settings for the timeline view. For now, the timescale
     * is fixed to a month view with 31 columns and a day unit.
     */
    initTimescale() {
      this.unit = 'day'
      this.timescale = 'month'
      this.visibleColumnCount = 31
      this.firstAvailableDate = moment
        .tz(this.timezone)
        .subtract(1, 'year')
        .startOf('year')
      this.lastAvailableDate = moment
        .tz(this.timezone)
        .add(1, 'year')
        .endOf('year')
    },
    /*
     * Returns the difference between two dates in the specified unit.
     */
    dateDiff(startDate, endDate, unit = this.unit, round = false) {
      return endDate.diff(startDate, unit, !round)
    },
    /*
     * Updates the grid based on the current scroll position.
     * If the column width has changed, we update it and recalculate the scroll offset
     * for today.
     */
    updateGridDimensions() {
      const el = this.scrollAreaElement
      this.gridWidth = el.clientWidth
      this.gridHeight = el.clientHeight
      this.columnWidth = Math.max(
        this.gridWidth / this.visibleColumnCount,
        this.minColumnWidth
      )
    },
    /*
     * Given the current horizontal scroll position, returns the range of visible columns.
     * This is used to determine which columns to render in the grid when the user scrolls
     * horizontally.
     */
    getVisibleColumnsRange() {
      const el = this.scrollAreaElement
      if (!el) {
        return { startIndex: 0, endIndex: 0 }
      }
      let startIndex = Math.floor(el.scrollLeft / this.columnWidth)
      let endIndex = startIndex + this.visibleColumnCount + 1
      if (endIndex > this.columns.length) {
        endIndex = this.columns.length
        startIndex = Math.max(0, endIndex - this.visibleColumnCount)
      }
      return { startIndex, endIndex }
    },
    /*
     * Initialize the grid columns with dates based on the timescale settings.
     */
    initGridColumns() {
      this.columns = Array.from(
        {
          length:
            this.dateDiff(this.firstAvailableDate, this.lastAvailableDate) + 1,
        },
        (_, i) => {
          const date = moment(this.firstAvailableDate).add(i, this.unit)
          return {
            id: i,
            date,
            isWeekend: date.isoWeekday() > 5,
          }
        }
      )
    },
    /**
     * Updates the grid columns when the container is resized. It also scrolls the grid
     * to the first visible date to ensure the user keeps their context.
     */
    onResizeUpdateGridColumns() {
      this.updateGridDimensions()

      // If the firstVisibleDate is not set yet, initialize it to the first date of the
      // current timescale.
      if (this.firstVisibleDate === null) {
        const firstDate = moment.tz(this.timezone).startOf(this.timescale)
        this.firstVisibleDate = firstDate
        this.$nextTick(() => {
          this.scrollDateIntoView(firstDate, 'instant')
        })
      }
    },
    /**
     * Updates the grid columns when the user scrolls horizontally. Updates the
     * columnsBuffer to show the right columns and updates the firstVisibleDate to
     * follow the scroll.
     */
    onHorizontalScrollUpdateGridColumns() {
      const { startIndex, endIndex } = this.getVisibleColumnsRange()
      const visibleColumns = this.columns.slice(startIndex, endIndex)
      const getPosition = (col, pos) => ({
        left: (startIndex + pos) * this.columnWidth,
      })
      recycleSlots(this.columnsBuffer, visibleColumns, getPosition)
      orderSlots(this.columnsBuffer, visibleColumns)
      // Pick index 1 because the startIndex is floored and we want to show the
      // first column entirely visible.
      this.firstVisibleDate = this.columnsBuffer[1].item.date
    },
    /**
     * Scrolls the grid horizontally to the specified position. It scrolls both the
     * grid body and the grid header to keep them in sync.
     */
    scrollLeft(left, behavior = 'instant') {
      this.scrollAreaElement.scroll({ left, behavior })
      this.$refs.gridHeader.scroll({ left, behavior })
    },
    /**
     * Scrolls the grid horizontally to the specified date.
     */
    scrollDateIntoView(date, behaviour = 'smooth') {
      const firstDate = this.firstAvailableDate
      const columnIndex = this.dateDiff(firstDate, date)
      this.scrollLeft(columnIndex * this.columnWidth, behaviour)
    },
  },
}
</script>
