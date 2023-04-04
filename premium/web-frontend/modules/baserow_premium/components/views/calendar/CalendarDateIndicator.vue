<template>
  <div class="calendar-date-indicator">{{ selectedMonth }}</div>
</template>

<script>
import { getCapitalizedMonthName } from '@baserow/modules/core/utils/date'

export default {
  name: 'CalendarDateIndicator',
  props: {
    selectedDate: {
      type: Object,
      required: true,
    },
  },
  computed: {
    selectedMonth() {
      return getCapitalizedMonthName(this.selectedDate)
    },
  },
}
</script>
