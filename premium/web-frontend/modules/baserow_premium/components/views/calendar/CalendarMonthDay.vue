<template>
  <li
    ref="calendarMonthDay"
    class="calendar-month-day"
    :class="{
      'calendar-month-day--not-current': !day.isCurrentMonth,
      'calendar-month-day--today': day.isToday,
      'calendar-month-day--weekend': day.isWeekend,
    }"
  >
    <a
      v-if="
        !readOnly &&
        $hasPermission(
          'database.table.create_row',
          table,
          database.workspace.id
        )
      "
      class="calendar-month-day__create-row-btn"
      @click="!readOnly && $emit('create-row', { day })"
      ><i class="fas fa-plus"></i>
    </a>
    <span ref="dateLabel" class="calendar-month-day__date-label">{{
      label
    }}</span>
    <div v-if="visibleRowsCount" class="calendar-month-day__cards">
      <CalendarCard
        v-for="row in visibleRows"
        :key="row.id"
        :row="row"
        :fields="fields"
        :store-prefix="storePrefix"
        @edit-row="$emit('edit-row', $event)"
      >
      </CalendarCard>
    </div>
    <a
      v-if="hiddenRowsCount > 0 && visibleRowsCalculated"
      class="calendar-month-day__more"
      @click="expand"
    >
      {{
        $tc('calendarMonthDay.hiddenRowsCount', hiddenRowsCount, {
          hiddenRowsCount,
        })
      }}
    </a>
    <CalendarMonthDayExpanded
      ref="calendarMonthDayExpanded"
      :day="day"
      :fields="fields"
      :store-prefix="storePrefix"
      :parent-width="width"
      :parent-height="height"
      @edit-row="$emit('edit-row', $event)"
    >
    </CalendarMonthDayExpanded>
  </li>
</template>

<script>
import moment from '@baserow/modules/core/moment'
import CalendarCard from '@baserow_premium/components/views/calendar/CalendarCard'
import CalendarMonthDayExpanded from '@baserow_premium/components/views/calendar/CalendarMonthDayExpanded'

export default {
  name: 'CalendarMonthDay',
  components: {
    CalendarCard,
    CalendarMonthDayExpanded,
  },
  props: {
    day: {
      type: Object,
      required: true,
    },
    storePrefix: {
      type: String,
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
      visibleRowsCalculated: false,
      visibleRowsCount: 0,
      height: 0,
      width: 0,
    }
  },
  computed: {
    label() {
      return moment(this.day.date).format('D')
    },
    dayStack() {
      const dayStack = this.$store.getters[
        this.storePrefix + 'view/calendar/getDateStack'
      ](this.day.dateString)
      return dayStack || { results: [], count: 0 }
    },
    rows() {
      return this.dayStack.results
    },
    rowsCount() {
      return this.dayStack.count
    },
    visibleRows() {
      return this.rows.slice(0, this.visibleRowsCount)
    },
    hiddenRowsCount() {
      return this.rowsCount - this.visibleRowsCount
    },
  },
  mounted() {
    this.updateVisibleRowsCount()
    window.addEventListener('resize', this.updateVisibleRowsCount)
  },
  beforeDestroy() {
    window.removeEventListener('resize', this.updateVisibleRowsCount)
  },
  methods: {
    updateVisibleRowsCount() {
      const itemHeight = 28
      this.width = this.$refs.calendarMonthDay.clientWidth
      this.height = this.$refs.calendarMonthDay.clientHeight
      let currentHeightWithItems = 30 + 8
      let count = 0
      while (currentHeightWithItems + itemHeight < this.height - 16 - 8) {
        count = count + 1
        currentHeightWithItems = currentHeightWithItems + itemHeight
      }
      this.visibleRowsCount = count
      this.visibleRowsCalculated = true
    },
    expand() {
      this.$refs.calendarMonthDayExpanded.show(
        this.$refs.calendarMonthDay,
        'bottom',
        'left',
        -(this.height - 2),
        -8
      )
    },
  },
}
</script>
