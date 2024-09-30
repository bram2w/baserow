<template>
  <div class="view-date-indicator">{{ selectedMonth }}</div>
</template>

<script>
import { getCapitalizedMonthName } from '@baserow/modules/core/utils/date'

export default {
  name: 'ViewDateIndicator',
  props: {
    selectedDate: {
      type: Object, // a moment object
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
